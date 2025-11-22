******************************************************************************************************************************
    집에서 최종 잘되던거  그리고 sql로 할껀지 자바로 할껀지 판단해야함 모두 테스트해봐야 스크립트도 추가
******************************************************************************************************************************

/**
 * =====================================================================
 * 📘 calculateVacationJS — 연차 흐름 계산기 (JavaScript 버전)
 * ---------------------------------------------------------------------
 * ▶ 역할
 *   - 한 사람의 연차 데이터 배열(vacList)을 받아서
 *   - 각 기간별로 FINAL_잔여일수, FINAL_사용합계, FINAL_사용이월,
 *     FINAL_지급합계, FINAL_지급이월 을 계산해서
 *   - 다시 vacList 안에 채워 넣어 주는 함수.
 *
 * ▶ 전제 조건 (매우 중요)
 *   1) vacList 는 "한 명(empno)"의 데이터만 들어 있어야 한다.
 *      - 즉, 사번별로 미리 나눠서 호출해야 한다.
 *      - 예: empno=2004109 에 대한 vacList 1개,
 *            empno=22000031 에 대한 vacList 1개, 이런 식.
 *
 *   2) vacList 는 VAC_FR_SORT(연차 시작일) 기준으로
 *      "오래된 순서 → 최신 순서" 로 이미 정렬되어 있어야 한다.
 *      - 예: 2023-01-01 → 2024-12-31 → 2025-12-31 ...
 *      - 이 순서가 바로 rn=1, rn=2, rn=3 과 같은 역할을 한다.
 *
 * ▶ 입력 컬럼 설명 (row 의 필수 키)
 *   - USABLE_VAC_DD_CNT      : 이번 기간에 사용할 수 있는 연차(잔여 기준)
 *   - USE_CNT                : 이번 기간에 실제로 사용한 연차
 *   - TOT_YY_VAC_DD_CNT      : 이번 기간에 지급된 연차 총합 (기본+가산 등)
 *   - APPROVED_CARRYOVER_DD  : 승인된 이월일수 (hw045m 기준, 없으면 0)
 *
 * ▶ 출력 컬럼 (이 함수가 채워주는 값)
 *   - FINAL_잔여일수
 *   - FINAL_사용합계
 *   - FINAL_사용이월
 *   - FINAL_지급합계
 *   - FINAL_지급이월
 *
 * ▶ 계산 규칙 (SQL 재귀 로직과 100% 동일)
 *   [첫 번째 기간] (i === 0, rn=1)
 *     - FINAL_잔여일수 = usable - approved
 *     - FINAL_사용합계 = useCnt + approved
 *     - FINAL_사용이월 = approved
 *     - FINAL_지급합계 = tot
 *     - FINAL_지급이월 = 0
 *
 *     → 첫 기간은 "이전 기간"이 없기 때문에,
 *       단지 승인 이월만 반영해서 잔여/사용을 잡고,
 *       지급합계는 tot 그대로 사용한다.
 *
 *   [다음 기간들] (i >= 1, rn>=2)
 *     - FINAL_지급합계 = tot + prevCarry
 *                       (이번 tot + 이전 기간의 승인 이월)
 *     - FINAL_사용합계 = useCnt + approved
 *     - FINAL_잔여일수 = FINAL_지급합계 - FINAL_사용합계
 *     - FINAL_사용이월 = approved
 *     - FINAL_지급이월 = prevCarry
 *
 *     → 이전 기간에서 넘어온 prevCarry(승인 이월)를
 *       이번 기간의 지급합계에 더해서 "지급이월" 효과를 준다.
 *       그리고 이번 기간의 승인 이월(approved)은
 *       다시 다음 기간으로 넘겨줄 준비(prevCarry 갱신).
 *
 * ▶ 핵심 요약
 *   - prevCarry 변수 하나로 "이전 기간에서 넘어온 이월"을 이어 준다.
 *   - 연도(YYYY)는 전혀 신경 쓰지 않고, VAC 시작일 순서만 본다.
 *   - 따라서 2023년에 이월, 2024년에 또 이월, 2025년에 또 이월 있어도
 *     전부 순서대로 정확하게 계산된다.
 *
 * =====================================================================
 */
function calculateVacationJS(vacList) {

    // vacList 는 이미 VAC_FR_SORT ASC 로 정렬되어 있다고 가정
    // (가장 오래된 연차 기간 → 그 다음 → 그 다음 ...)

    // prevCarry : "이전 기간의 승인 이월" 값을 들고 있다가
    //             다음 기간 계산에 사용되는 변수.
    //             (SQL 의 final_pay_carry 와 같은 역할)
    let prevCarry = 0;

    // vacList 의 각 기간(VAC 기간)을 순서대로 돌면서 계산
    for (let i = 0; i < vacList.length; i++) {

        let row = vacList[i];  // 현재 기간 한 줄 (DataSet 행처럼 사용)

        // 원본 값 숫자로 변환 (혹시 문자열일 수 있으므로 Number() 사용)
        let usable   = Number(row.USABLE_VAC_DD_CNT);      // 쓸 수 있는 연차(잔여 기준)
        let useCnt   = Number(row.USE_CNT);                // 이번 기간 사용 연차
        let tot      = Number(row.TOT_YY_VAC_DD_CNT);      // 이번 기간 지급 연차 합계
        let approved = Number(row.APPROVED_CARRYOVER_DD);  // 승인 이월 (없으면 0)

        if (i === 0) {
            // ============================================================
            // 🟦 첫 번째 기간 (rn=1 역할)
            //  - 이 기간은 "가장 오래된 VAC 기간"
            //  - 이전 기간이 없으므로 prevCarry 사용 안 함.
            //  - 승인 이월(approved)만 반영해서 계산.
            // ============================================================

            // 잔여 = 사용할 수 있는 연차 - 승인 이월
            let finalRemain = usable - approved;

            // 사용합계 = 실제 사용 + 승인 이월
            let finalUse    = useCnt + approved;

            // 지급합계 = 이번 기간 지급량(tot) 그대로
            let finalPay    = tot;

            // 현재 row 에 결과값 저장
            row.FINAL_잔여일수  = finalRemain;
            row.FINAL_사용합계  = finalUse;
            row.FINAL_사용이월  = approved;  // 이 기간에서 다음으로 넘길 "승인 이월"
            row.FINAL_지급합계  = finalPay;
            row.FINAL_지급이월  = 0;         // 첫 기간은 이전 이월이 없으므로 0

            // 다음 기간에서 사용할 prevCarry 는
            // "이번 기간의 승인 이월" 이 된다.
            prevCarry = approved;

        } else {
            // ============================================================
            // 🟩 두 번째 기간 이후 (rn>=2 역할)
            //  - 이전 기간에서 넘어온 prevCarry 를 더해서 지급합계를 만든다.
            //  - 이번 기간의 승인 이월(approved)은 다음 기간을 위해 남겨둔다.
            // ============================================================

            // 지급합계 = 이번 기간 지급량 + 이전 기간의 승인 이월
            let finalPay = tot + prevCarry;

            // 사용합계 = 이번 사용량 + 이번 승인 이월
            let finalUse = useCnt + approved;

            // 잔여일수 = 지급합계 - 사용합계
            let finalRemain = finalPay - finalUse;

            // 현재 row 에 결과값 저장
            row.FINAL_잔여일수  = finalRemain;
            row.FINAL_사용합계  = finalUse;
            row.FINAL_사용이월  = approved;   // 이번 기간 승인 이월
            row.FINAL_지급합계  = finalPay;
            row.FINAL_지급이월  = prevCarry;  // 이전 기간에서 넘어온 이월

            // 다음 기간에서 사용할 prevCarry 갱신
            // (다음 기간 기준으로 "이전 승인 이월"은 이번 approved)
            prevCarry = approved;
        }
    }

    // vacList 내부 row 들에 FINAL_* 이 모두 채워진 상태로 반환
    return vacList;
}

    
===================================================================================================================================
/**
 * =====================================================================
 * 📘 calculateVacation — "연차 흐름 자동 계산기"
 * ---------------------------------------------------------------------
 * 이 함수는 SQL 재귀(RecursiveCalc)와 100% 동일한 방식으로
 * VAC 기간 순서대로 연차 흐름을 계산하는 로직이다.
 *
 * vacList 데이터는 이미 다음처럼 들어온다:
 *   - USABLE_VAC_DD_CNT : 이번 기간에서 쓸 수 있는 연차
 *   - USE_CNT           : 이번 기간에 실제로 사용한 연차
 *   - TOT_YY_VAC_DD_CNT : 이번 기간에 지급된 연차 총합
 *   - APPROVED_CARRYOVER_DD : 승인된 이월(전년도에서 넘어온 일수)
 *
 * 📌 이 함수가 하는 일 (초등학생 버전)
 * ---------------------------------------------------------------------
 * 1) vacList 는 VAC_FR_SORT(연차기간 시작일) 기준으로 이미 정렬되어 있다.
 *    → 즉, 가장 오래된 연차부터 순서대로 들어 있다.
 *
 * 2) 첫 번째 기간(i == 0)은 "첫 연차 기간"이므로 이월 계산할 게 없다.
 *    단지 승인된 이월(approved)만 적용한다.
 *
 * 3) 두 번째 기간부터(i >= 1)는
 *    바로 이전 기간의 승인 이월(prevCarry)을 받아서
 *    지급합계(tot + prevCarry)에 더한다.
 *
 * 4) 각 기간은 다음 5가지를 계산해서 row.put() 으로 저장한다:
 *       - FINAL_잔여일수
 *       - FINAL_사용합계
 *       - FINAL_사용이월
 *       - FINAL_지급합계
 *       - FINAL_지급이월
 *
 * 5) prevCarry 는 "이번 기간의 승인 이월"을 다음 기간으로 넘긴다.
 *
 * 즉, 연차는 아래처럼 흐른다:
 *
 *     [기간1 승인 이월] → 기간2 계산에 사용됨
 *     [기간2 승인 이월] → 기간3 계산에 사용됨
 *     [기간3 승인 이월] → 기간4 계산에 사용됨
 *
 * ✔ 그래서 2023년에 이월 있고, 2024년에 또 있고, 2025년에 있어도  
 *   모두 문제 없이 정확하게 계산된다.
 *
 * ✔ 연도는 전혀 중요하지 않으며  
 *   VAC 기간 순서(i 순서)가 절대 기준이다.
 *
 * =====================================================================
 */
public List<DataSet> calculateVacation(List<DataSet> vacList) {

    // vacList 는 이미 VAC_FR_SORT ASC 로 정렬되어 있다고 가정
    // 예: 가장 오래된 연차 -> 중간 기간 -> 최신 기간

    double prevCarry = 0;   // 이전 기간의 FINAL_사용이월 (SQL의 final_pay_carry 와 동일)

    for (int i = 0; i < vacList.size(); i++) {

        DataSet row = vacList.get(i);

        // 원본 값 가져오기
        double usable   = row.getDouble("USABLE_VAC_DD_CNT");   // 쓸 수 있는 연차
        double useCnt   = row.getDouble("USE_CNT");             // 이번 기간 사용 연차
        double tot      = row.getDouble("TOT_YY_VAC_DD_CNT");   // 이번 기간 지급 연차
        double approved = row.getDouble("APPROVED_CARRYOVER_DD"); // 승인된 이월(전년도에서 넘어온 일수)

        if (i == 0) {  
            // ============================================================
            // 📌 첫 번째 기간 (rn=1)
            // VAC 기간 중 가장 오래된 기간 (SQL 재귀와 동일)
            // ============================================================

            double finalRemain = usable - approved;   // 잔여일 = 사용 가능 - 승인 이월
            double finalUse    = useCnt + approved;   // 사용합계 = 원래 사용 + 승인 이월
            double finalPay    = tot;                 // 지급합계 = tot 그대로 (첫 기간은 이월 합산 없음)

            // 결과 저장
            row.put("FINAL_잔여일수", finalRemain);
            row.put("FINAL_사용합계", finalUse);
            row.put("FINAL_사용이월", approved);  // 승인 이월 자체
            row.put("FINAL_지급합계", finalPay);
            row.put("FINAL_지급이월", 0);         // 첫 기간은 이전 이월이 없음

            // 다음 기간으로 넘길 이월은 "승인이월" 자체
            prevCarry = approved;

        } else {  
            // ============================================================
            // 📌 두 번째 기간 이후 (rn >= 2)
            // 이전 기간의 승인 이월(prevCarry)을 이번 지급에 더해야 함
            // ============================================================

            double finalPay     = tot + prevCarry;     // 지급합계 = tot + 이전 이월
            double finalUse     = useCnt + approved;   // 사용합계 = 사용 + 승인 이월
            double finalRemain  = finalPay - finalUse; // 잔여일 = 지급합계 - 사용합계

            // 결과 저장
            row.put("FINAL_잔여일수", finalRemain);
            row.put("FINAL_사용합계", finalUse);
            row.put("FINAL_사용이월", approved);     // 이번 승인 이월
            row.put("FINAL_지급합계", finalPay);    // 이번 지급 합계
            row.put("FINAL_지급이월", prevCarry);    // 이전 기간에서 넘어온 이월

            // 다음 기간으로 넘겨줄 이월은 "이번 승인 이월"
            prevCarry = approved;
        }
    }

    return vacList;
}

    
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////




    
/* ======================================================================
 * 💡 초등학생도 이해할 수 있는 초초상세 설명 + (왜 alias 가 필수인지 포함)
 * ----------------------------------------------------------------------
 * 이 쿼리는 "연차가 해마다 어떻게 흘러가는지"를 정확하게 계산하는
 * 완전 자동 연차 흐름 계산기예요.
 *
 * 직원마다 다음 데이터가 와요:
 *   - 연차 시작일(VAC_FR)
 *   - 연차 종료일(VAC_TO)
 *   - 그 해 지급된 연차
 *   - 사용한 연차
 *   - 남은 연차
 *   - 신청한 이월일수(REQ_DD_CNT)
 *
 * 이걸 단순히 연도별로 SUM 하거나 ORDER BY 하면 절대 안 돼요.
 * 왜냐면 김근수처럼,
 *   ✔ 연도는 2023, 2024, 2025로 다르지만
 *   ✔ 연차 기간(VAC_FR ~ VAC_TO)은 똑같은 사람이 있기 때문이에요.
 *
 * 이런 사람은 "같은 기간의 연차를 여러 번 받은 것처럼 보이지만"
 * 실제로는 "1개의 기간"만 존재하는 것이므로,
 * 반드시 1번만 계산해야 해요.
 *
 * 그래서 이 쿼리는 전체 5단계 구조로 동작해요.
 *
 * ----------------------------------------------------------------------
 * ⭐ 1단계: BaseData
 * ----------------------------------------------------------------------
 * hp040d(연차기본) + hw045m(이월신청)을 LEFT JOIN 해서
 * 모든 원본 연차 데이터를 가져와요.
 *
 *  ✔ 여기서 alias(별칭)가 꼭 필요한 3개 컬럼
 *  ---------------------------------------------------------
 *   1) T.yy_vac_fr  →  vac_fr_sort
 *   2) T.yy_vac_to  →  vac_to_sort
 *   3) NVL(R.req_dd_cnt,0) → approved_carryover_dd
 *
 *  왜 반드시 별칭이 필요할까?
 *  ---------------------------------------------------------
 *  ❗ vac_fr_sort / vac_to_sort
 *     - 기간 순으로 정렬해야 하고
 *     - 중복 기간 묶는 기준이기 때문에 필수.
 *     - 원본 컬럼명은 GROUP BY·JOIN 과정에서 직접 사용이 어려움.
 *
 *  ❗ approved_carryover_dd
 *     - NVL() 표현식은 컬럼명이 없기 때문에 alias 없으면 이후 단계에서 사용 불가.
 *     - 재귀 계산에서 반드시 직접 컬럼처럼 써야 함.
 *
 * ----------------------------------------------------------------------
 * ⭐ 2단계: VacGroup (중복 VAC 기간 제거)
 * ----------------------------------------------------------------------
 * 동일한 VAC_FR ~ VAC_TO 기간이 여러 번 있어도 연차는 1번만 계산해야 함.
 *
 * 예) 김근수  
 *   - 2023 데이터  
 *   - 2024 데이터  
 *   - 2025 데이터  
 *   → 기간이 같으므로 실제로는 1개로 묶어야 함.
 *
 * SUM 쓰면 전부 더해져서 망함.
 * 그래서 MAX 로 1개만 남김.
 *
 * ----------------------------------------------------------------------
 * ⭐ 3단계: VacRank (기간 순서대로 번호 부여)
 * ----------------------------------------------------------------------
 * VAC 시작일(vac_fr_sort)을 기준으로 오래된 순서대로
 *   rn=1, rn=2, rn=3 … 번호를 붙인다.
 *
 * 이 번호로 재귀 계산 순서가 정해짐.
 *
 * ----------------------------------------------------------------------
 * ⭐ 4단계: RecursiveCalc (연차 흐름 재귀 공식)
 * ----------------------------------------------------------------------
 * 여기에서 실제로 "연차가 어떻게 넘어가는지"를 계산함.
 *
 * ✔ 첫 번째 기간(rn=1)
 *     잔여 = usable - approved
 *     사용합계 = use_cnt + approved
 *     지급합계 = tot 그대로
 *
 * ✔ 다음 기간들(rn>=2)
 *     이전 기간의 이월(final_pay_carry)을 더해 계산
 *
 * 이 구조 덕분에:
 *   - 기간이 나눠진 유림 케이스
 *   - 기간은 같지만 연도만 다른 김근수 케이스
 * 전부 정확히 계산됨.
 *
 * ⚠ 중요: "연도(YYYY)는 의미 없음"  
 *          오직 VAC 기간이 계산 기준임.
 *
 * ----------------------------------------------------------------------
 * ⭐ 5단계: FinalResult
 * ----------------------------------------------------------------------
 * BaseData의 원본 값 + 재귀 계산 FINAL_* 값 합쳐서 최종 출력.
 *
 * ----------------------------------------------------------------------
 * 💛 결론
 * ----------------------------------------------------------------------
 * ✔ 사원이 1명이든 1,000명이든  
 * ✔ 연도가 뒤죽박죽이어도  
 * ✔ VAC 기간이 중복되어도  
 * ✔ 이월이 특정 연도에 몰려 있어도  
 *
 * 이 쿼리는 기간기준 + 재귀 로직으로 100% 정확하게 계산됨.
 *
 * ====================================================================== */



WITH BaseData AS (
    SELECT
        T.yyyy,
        T.entity,
        T.empno,
        T.empnm,
        T.biz_section,
        T.dept_nm,
        T.paycd_nm,
        T.paygd1_nm,
        T.poscd,
        T.entdt,
        T.retdt,

        /* VAC 기간 (정렬/그룹핑의 절대 기준) */
        T.yy_vac_fr  AS vac_fr_sort,
        T.yy_vac_to  AS vac_to_sort,

        /* 원본 값들 */
        T.usable_vac_dd_cnt,
        T.use_cnt,
        T.tot_yy_vac_dd_cnt,

        /* 승인된 이월일수 */
        NVL(R.req_dd_cnt,0) AS approved_carryover_dd

    FROM hp040d T
    LEFT JOIN hw045m R
      ON T.empno = R.req_empno
     AND T.yy_vac_fr = R.occr_date
),


/* 중복 VAC 기간 제거 (SUM 금지 → 반드시 MAX 로 1개만 유지) */
VacGroup AS (
    SELECT
        empno,
        vac_fr_sort,
        vac_to_sort,
        MAX(usable_vac_dd_cnt) AS usable_vac_dd_cnt,
        MAX(use_cnt)           AS use_cnt,
        MAX(tot_yy_vac_dd_cnt) AS tot_yy_vac_dd_cnt,
        MAX(approved_carryover_dd) AS approved_carryover_dd
    FROM BaseData
    GROUP BY empno, vac_fr_sort, vac_to_sort
),


/* 오래된 기간 순서대로 rn=1,2,3... 부여 */
VacRank AS (
    SELECT
        V.*,
        ROW_NUMBER() OVER(
            PARTITION BY empno
            ORDER BY vac_fr_sort ASC
        ) AS rn
    FROM VacGroup V
),


CalcInput AS (
    SELECT *
    FROM VacRank
),


/* 재귀로 연차 흐름 전체 계산 */
RecursiveCalc (
    empno, rn,
    final_pay_carry,     -- 지급이월
    final_pay_total,     -- 지급합계
    final_use_total,     -- 사용합계
    final_remain         -- 잔여일수
) AS (

/* ----------------------------------------------------------------------
 * 📌 rn=1 은 VAC_FR 기준으로 가장 오래된 기간이다 (연도와 무관).
 *
 * 예시: 김근수
 *
 *  -----------------------------------------------------------
 *  | 데이터 |     VAC_FR     |     VAC_TO     |      결과      |
 *  |--------|----------------|----------------|----------------|
 *  | 2023   | 2023-01-01     | 2024-12-30     |  rn=1          |
 *  | 2024   | 2024-12-31     | 2025-12-30     |  rn=2          |
 *  | 2025   | 2024-12-31     | 2025-12-30     |  rn=2 그룹 포함 |
 *  -----------------------------------------------------------
 *
 * ✔ 정리
 *   - rn=1: 가장 오래된 VAC 기간
 *   - rn>=2: 이후 VAC 기간
 *   - 연도(YYYY)는 계산에 단 1도 영향 없음
 *   - 같은 기간은 VacGroup에서 하나로 묶임
 * ---------------------------------------------------------------------- */

    /* 첫 번째 기간 */
    SELECT
        empno,
        rn,
        approved_carryover_dd,                        -- 지급이월
        tot_yy_vac_dd_cnt,                            -- 지급합계
        (use_cnt + approved_carryover_dd),            -- 사용합계
        (usable_vac_dd_cnt - approved_carryover_dd)   -- 잔여일수
    FROM CalcInput
    WHERE rn = 1

    UNION ALL

    /* 다음 기간 (rn>=2) */
    SELECT
        C.empno,
        C.rn,
        C.approved_carryover_dd,
        (C.tot_yy_vac_dd_cnt + R.final_pay_carry),
        (C.use_cnt + C.approved_carryover_dd),
        ( (C.tot_yy_vac_dd_cnt + R.final_pay_carry)
          - (C.use_cnt + C.approved_carryover_dd) )
    FROM CalcInput C
    JOIN RecursiveCalc R
      ON C.empno = R.empno
     AND C.rn   = R.rn + 1
),


/* 최종 결과 조합 */
FinalResult AS (
    SELECT
         B.YYYY
        ,B.ENTITY
        ,B.EMPNO
        ,B.EMPNM
        ,B.DEPT_NM
        ,B.BIZ_SECTION
        ,B.PAYCD_NM
        ,B.PAYGD1_NM
        ,B.POSCD
        ,B.ENTDT
        ,B.RETDT

        ,B.VAC_FR_SORT
        ,B.VAC_TO_SORT

        ,B.USABLE_VAC_DD_CNT
        ,B.USE_CNT
        ,B.TOT_YY_VAC_DD_CNT
        ,B.APPROVED_CARRYOVER_DD
        ,' ------ '

        ,R.final_remain              AS FINAL_잔여일수
        ,R.final_use_total           AS FINAL_사용합계
        ,R.final_pay_carry           AS FINAL_사용이월
        ,R.final_pay_total           AS FINAL_지급합계
        ,R.final_pay_carry           AS FINAL_지급이월

        ,V.rn
    FROM BaseData B
    JOIN VacRank V
        ON B.empno = V.empno
       AND B.vac_fr_sort = V.vac_fr_sort
    LEFT JOIN RecursiveCalc R
        ON V.empno = R.empno
       AND V.rn = R.rn
)

SELECT *
FROM FinalResult
ORDER BY empno, YYYY DESC;








******************************************************************************************************************************






















/* ======================================================================
 * my_select_FINAL_v7.2
 * 요구사항 완전 반영:
 * - VAC 기간 중복 계산 1회
 * - 첫년도(rn=1): 잔여 = usable_vac_dd_cnt - approved_carryover_dd
 * - 다음 년도(rn>=2): 지급합계 = tot + 이전 FINAL_사용이월
 * - FINAL_* 순서 유지
 * - ORA-00918 없음
 * ====================================================================== */

WITH BaseData AS (
    SELECT
        T.yyyy,
        T.entity,
        T.empno,
        T.empnm,
        T.dept_nm,
        T.biz_section, T.paycd_nm, T.paygd1_nm, T.poscd,
        T.entdt, T.retdt,

        T.yy_vac_fr AS VAC_FR_SORT,
        T.yy_vac_to AS VAC_TO_SORT,

       T.yy_vac_fr_to,
        T.vac_list_yy_fr, T.vac_list_yy_to,
        T.vac_list_mm_fr, T.vac_list_mm_to,

        ----------------------------------------------
        T.usable_vac_dd_cnt, -- 잔여일수
        ----------------------------------------------

        ----------------------------------------------
        -- 사용정보 그룹
        ----------------------------------------------
         T.use_cnt,		-- 사용일수 합계
        T.year_use_cnt,          -- 년차 사용
        T.half_use_cnt,           -- 반차 사용
        T.half_half_use_cnt,     -- 반반차 사용

        ----------------------------------------------
        -- 지급정보 그룹
        ----------------------------------------------
        T.tot_yy_vac_dd_cnt,     -- 지급일수 합계 
        T.yy_vac_dd_cnt,          -- 기본 부여 일수
        T.yy_vac_dd_cnt_add,    -- 근속 가산 일수
        T.yy_vac_dd_cnt_adj,     -- 조정 일수
        T.yy_vac_dd_cnt_sub,    -- 차감
        

        CASE
            WHEN NVL(R.req_dd_cnt,0) <= T.usable_vac_dd_cnt
            THEN NVL(R.req_dd_cnt,0)
            ELSE 0
        END AS approved_carryover_dd

    FROM hp040d T
    LEFT JOIN hw045m R
      ON T.empno = R.req_empno
     AND T.yy_vac_fr = R.occr_date
),

DistinctVac AS (
    SELECT DISTINCT
        empno,
        VAC_FR_SORT,
        VAC_TO_SORT,
        use_cnt,
        tot_yy_vac_dd_cnt,
        usable_vac_dd_cnt,
        approved_carryover_dd
    FROM BaseData
),

DistinctRanked AS (
    SELECT
        D.*,
        ROW_NUMBER() OVER (
            PARTITION BY empno
            ORDER BY VAC_FR_SORT ASC
        ) AS rn
    FROM DistinctVac D
),

CalcInput AS (
    SELECT
        empno, rn,
        VAC_FR_SORT, VAC_TO_SORT,
        use_cnt,
        tot_yy_vac_dd_cnt,
        usable_vac_dd_cnt,
        approved_carryover_dd
    FROM DistinctRanked
),

/* ======================================================================
 * 재귀 계산
 * ====================================================================== */
RecursiveResult (
    empno, rn,
    FINAL_잔여일수,
    FINAL_사용합계,
    FINAL_사용이월,
    FINAL_지급합계,
    FINAL_지급이월
) AS (

    /* ----------------------- rn = 1 ----------------------- */
    SELECT
        empno,
        rn,

        /* FINAL_잔여일수 = usable - approved_carryover */
        (usable_vac_dd_cnt - approved_carryover_dd),

        /* FINAL_사용합계 = 원본 use_cnt */
        use_cnt,

        /* FINAL_사용이월 = approved_carryover_dd */
        approved_carryover_dd,

        /* FINAL_지급합계 = tot 그대로 */
        tot_yy_vac_dd_cnt,

        /* FINAL_지급이월 = 0 */
        0

    FROM CalcInput
    WHERE rn = 1

    UNION ALL

    /* ----------------------- rn >= 2 ----------------------- */
    SELECT
        I.empno,
        I.rn,

        /* FINAL_잔여일수 = 지급합계 - 사용합계 */
        (I.tot_yy_vac_dd_cnt + R.FINAL_사용이월) - I.use_cnt,

        /* FINAL_사용합계 */
        I.use_cnt,

        /* FINAL_사용이월 (자기 자신의 승인 이월분) */
        I.approved_carryover_dd,

        /* FINAL_지급합계 = tot + 이전 사용이월 */
        (I.tot_yy_vac_dd_cnt + R.FINAL_사용이월),

        /* FINAL_지급이월 = R.FINAL_사용이월 */
        R.FINAL_사용이월

    FROM CalcInput I
    JOIN RecursiveResult R
      ON I.empno = R.empno
     AND I.rn = R.rn + 1
),

/* ======================================================================
 * 최종 조합
 * ====================================================================== */
FinalResult AS (
    SELECT
         B.YYYY
        , B.ENTITY
        , B.EMPNO
        , B.EMPNM
        , B.DEPT_NM
        , B.BIZ_SECTION
        , B.PAYCD_NM
        , B.PAYGD1_NM
        , B.POSCD
        , B.ENTDT
        , B.RETDT
        
        , B.VAC_FR_SORT
        , B.VAC_TO_SORT
        
        , B.VAC_LIST_YY_FR
        , B.VAC_LIST_YY_TO
        , B.VAC_LIST_MM_FR
        , B.VAC_LIST_MM_TO
        
         , B.USABLE_VAC_DD_CNT  -- 잔여일수
        --------------------------------------------------------------
        -- 사용 그룹
        --------------------------------------------------------------        
        , B.USE_CNT             -- 사용일수  합계
        , B.YEAR_USE_CNT        -- 년차 사용
        , B.HALF_USE_CNT        -- 반차 사용
        , B.HALF_HALF_USE_CNT   -- 반반차 사용
        
        
        --------------------------------------------------------------
        -- 지급 그룹
        --------------------------------------------------------------   
        , B.TOT_YY_VAC_DD_CNT -- 지급일수 합계    
       
        , B.YY_VAC_DD_CNT           -- 기본 부여 일수
        , B.YY_VAC_DD_CNT_ADD       -- 근속 가산 일수
        , B.YY_VAC_DD_CNT_ADJ       -- 조정 일수
        , B.YY_VAC_DD_CNT_SUB       -- 지급일수 > 차감
        
        
        , B.APPROVED_CARRYOVER_DD  -- 이월신청일수
        
        ,' ------ '
        
     , R.FINAL_잔여일수 -- 잔여일수
        --------------------------------------------------------------
        -- 사용 그룹
        --------------------------------------------------------------        
        ,R.FINAL_사용합계             -- 사용일수  합계
        ,B.YEAR_USE_CNT   AS  FINAL_YEAR_USE_CNT    -- 년차 사용
        ,B.HALF_USE_CNT     AS FINAL_HALF_USE_CNT     -- 반차 사용
        ,B.HALF_HALF_USE_CNT   AS FINAL_HALF_HALF_USE_CNT -- 반반차 사용
        ,R.FINAL_사용이월
        
        --------------------------------------------------------------
        -- 지급 그룹
        --------------------------------------------------------------   
        , R.FINAL_지급합계 -- 지급일수 합계    
       
        , B.YY_VAC_DD_CNT       AS FINAL_YY_VAC_DD_CNT      -- 기본 부여 일수
        , B.YY_VAC_DD_CNT_ADD     AS FINAL_YY_VAC_DD_CNT_ADD   -- 근속 가산 일수
        , B.YY_VAC_DD_CNT_ADJ   AS FINAL_YY_VAC_DD_CNT_ADJ     -- 조정 일수
        , B.YY_VAC_DD_CNT_SUB  AS FINAL_YY_VAC_DD_CNT_SUB     -- 지급일수 > 차감
        , R.FINAL_지급이월
        
        
        
--        ,R.FINAL_잔여일수
--        ,R.FINAL_사용합계
--        ,R.FINAL_사용이월
--        ,R.FINAL_지급합계
--        ,R.FINAL_지급이월
        ,D.rn
    FROM BaseData B
    JOIN DistinctRanked D
      ON B.empno = D.empno
     AND B.VAC_FR_SORT = D.VAC_FR_SORT
    LEFT JOIN RecursiveResult R
      ON D.empno = R.empno
     AND D.rn = R.rn
)

SELECT *
FROM FinalResult
ORDER BY empno, VAC_FR_SORT DESC;

-----------------------------------------------------------------------------------------------------------------------------------------------

INSERT INTO "MYBASEUSER"."HP040D" (YYYY, ENTITY, EMPNO, EMPNM, BIZ_SECTION, DEPT_NM, PAYCD_NM, PAYGD1_NM, POSCD, ENTDT, YY_VAC_FR, YY_VAC_TO, YY_VAC_FR_TO, VAC_LIST_YY_FR, VAC_LIST_YY_TO, USABLE_VAC_DD_CNT, USE_CNT, YEAR_USE_CNT, HALF_USE_CNT, HALF_HALF_USE_CNT, TOT_YY_VAC_DD_CNT, YY_VAC_DD_CNT, YY_VAC_DD_CNT_ADD, YY_VAC_DD_CNT_ADJ, YY_VAC_DD_CNT_SUB) VALUES ('2023', '2022', '2004109', '유림', '7', '전북지사', '월급직', '전임 9등급', '12', '2020-11-30', '2023-11-16', '2024-11-15', '2023-11-16 ~ 2024-11-15', '2023-11-16', '2024-11-15', '0', '16', '14', '1', '1', '16', '15', '1', '0', '0')

커밋 성공



/* ======================================================================
 * my_select_FINAL_v7.2
 * 요구사항 완전 반영:
 * - VAC 기간 중복 계산 1회
 * - 첫년도(rn=1): 잔여 = usable_vac_dd_cnt - approved_carryover_dd
 * - 다음 년도(rn>=2): 지급합계 = tot + 이전 FINAL_사용이월
 * - FINAL_* 순서 유지
 * - ORA-00918 없음
 * ====================================================================== */

WITH BaseData AS (
    SELECT
        T.yyyy,
        T.entity,
        T.empno,
        T.empnm,
        T.dept_nm,
        T.use_cnt,
        T.tot_yy_vac_dd_cnt,
        T.usable_vac_dd_cnt,

        T.yy_vac_fr AS VAC_FR_SORT,
        T.yy_vac_to AS VAC_TO_SORT,

        T.biz_section, T.paycd_nm, T.paygd1_nm, T.poscd,
        T.entdt, T.retdt, T.yy_vac_fr_to,
        T.vac_list_yy_fr, T.vac_list_yy_to,
        T.vac_list_mm_fr, T.vac_list_mm_to,
        T.year_use_cnt, T.half_use_cnt, T.half_half_use_cnt,
        T.yy_vac_dd_cnt, T.yy_vac_dd_cnt_add,
        T.yy_vac_dd_cnt_adj, T.yy_vac_dd_cnt_sub,
        0 AS req_dd_cnt,
        0 AS yy_req_dd_cnt,

        CASE
            WHEN NVL(R.req_dd_cnt,0) <= T.usable_vac_dd_cnt
            THEN NVL(R.req_dd_cnt,0)
            ELSE 0
        END AS approved_carryover_dd

    FROM hp040d T
    LEFT JOIN hw045m R
      ON T.empno = R.req_empno
     AND T.yy_vac_fr = R.occr_date
),

DistinctVac AS (
    SELECT DISTINCT
        empno,
        VAC_FR_SORT,
        VAC_TO_SORT,
        use_cnt,
        tot_yy_vac_dd_cnt,
        usable_vac_dd_cnt,
        approved_carryover_dd
    FROM BaseData
),

DistinctRanked AS (
    SELECT
        D.*,
        ROW_NUMBER() OVER (
            PARTITION BY empno
            ORDER BY VAC_FR_SORT ASC
        ) AS rn
    FROM DistinctVac D
),

CalcInput AS (
    SELECT
        empno, rn,
        VAC_FR_SORT, VAC_TO_SORT,
        use_cnt,
        tot_yy_vac_dd_cnt,
        usable_vac_dd_cnt,
        approved_carryover_dd
    FROM DistinctRanked
),

/* ======================================================================
 * 재귀 계산
 * ====================================================================== */
RecursiveResult (
    empno, rn,
    FINAL_잔여일수,
    FINAL_사용합계,
    FINAL_사용이월,
    FINAL_지급합계,
    FINAL_지급이월
) AS (

    /* ----------------------- rn = 1 ----------------------- */
    SELECT
        empno,
        rn,

        /* FINAL_잔여일수 = usable - approved_carryover */
        (usable_vac_dd_cnt - approved_carryover_dd),

        /* FINAL_사용합계 = 원본 use_cnt */
        use_cnt,

        /* FINAL_사용이월 = approved_carryover_dd */
        approved_carryover_dd,

        /* FINAL_지급합계 = tot 그대로 */
        tot_yy_vac_dd_cnt,

        /* FINAL_지급이월 = 0 */
        0

    FROM CalcInput
    WHERE rn = 1

    UNION ALL

    /* ----------------------- rn >= 2 ----------------------- */
    SELECT
        I.empno,
        I.rn,

        /* FINAL_잔여일수 = 지급합계 - 사용합계 */
        (I.tot_yy_vac_dd_cnt + R.FINAL_사용이월) - I.use_cnt,

        /* FINAL_사용합계 */
        I.use_cnt,

        /* FINAL_사용이월 (자기 자신의 승인 이월분) */
        I.approved_carryover_dd,

        /* FINAL_지급합계 = tot + 이전 사용이월 */
        (I.tot_yy_vac_dd_cnt + R.FINAL_사용이월),

        /* FINAL_지급이월 = R.FINAL_사용이월 */
        R.FINAL_사용이월

    FROM CalcInput I
    JOIN RecursiveResult R
      ON I.empno = R.empno
     AND I.rn = R.rn + 1
),

/* ======================================================================
 * 최종 조합
 * ====================================================================== */
FinalResult AS (
    SELECT
         B.YYYY
        , B.ENTITY
        , B.EMPNO
        , B.EMPNM
        , B.DEPT_NM
        , B.BIZ_SECTION
        , B.PAYCD_NM
        , B.PAYGD1_NM
        , B.POSCD
        , B.ENTDT
        , B.RETDT
        
        , B.VAC_FR_SORT
        , B.VAC_TO_SORT
        
        , B.VAC_LIST_YY_FR
        , B.VAC_LIST_YY_TO
        , B.VAC_LIST_MM_FR
        , B.VAC_LIST_MM_TO
        
         , B.USABLE_VAC_DD_CNT  -- 잔여일수
        --------------------------------------------------------------
        -- 사용 그룹
        --------------------------------------------------------------        
        , B.USE_CNT             -- 사용일수  합계
        , B.YEAR_USE_CNT        -- 년차 사용
        , B.HALF_USE_CNT        -- 반차 사용
        , B.HALF_HALF_USE_CNT   -- 반반차 사용
        
        
        --------------------------------------------------------------
        -- 지급 그룹
        --------------------------------------------------------------   
        , B.TOT_YY_VAC_DD_CNT -- 지급일수 합계    
       
        , B.YY_VAC_DD_CNT           -- 기본 부여 일수
        , B.YY_VAC_DD_CNT_ADD       -- 근속 가산 일수
        , B.YY_VAC_DD_CNT_ADJ       -- 조정 일수
        , B.YY_VAC_DD_CNT_SUB       -- 지급일수 > 차감
        
        
        , B.APPROVED_CARRYOVER_DD  -- 이월신청일수
        
        ,' ------ '
        
     , R.FINAL_잔여일수 -- 잔여일수
        --------------------------------------------------------------
        -- 사용 그룹
        --------------------------------------------------------------        
        ,R.FINAL_사용합계             -- 사용일수  합계
        ,B.YEAR_USE_CNT   AS  FINAL_YEAR_USE_CNT    -- 년차 사용
        ,B.HALF_USE_CNT     AS FINAL_HALF_USE_CNT     -- 반차 사용
        ,B.HALF_HALF_USE_CNT   AS FINAL_HALF_HALF_USE_CNT -- 반반차 사용
        ,R.FINAL_사용이월
        
        --------------------------------------------------------------
        -- 지급 그룹
        --------------------------------------------------------------   
        , R.FINAL_지급합계 -- 지급일수 합계    
       
        , B.YY_VAC_DD_CNT       AS FINAL_YY_VAC_DD_CNT      -- 기본 부여 일수
        , B.YY_VAC_DD_CNT_ADD     AS FINAL_YY_VAC_DD_CNT_ADD   -- 근속 가산 일수
        , B.YY_VAC_DD_CNT_ADJ   AS FINAL_YY_VAC_DD_CNT_ADJ     -- 조정 일수
        , B.YY_VAC_DD_CNT_SUB  AS FINAL_YY_VAC_DD_CNT_SUB     -- 지급일수 > 차감
        , R.FINAL_지급이월
        
        
        
--        ,R.FINAL_잔여일수
--        ,R.FINAL_사용합계
--        ,R.FINAL_사용이월
--        ,R.FINAL_지급합계
--        ,R.FINAL_지급이월
        ,D.rn
    FROM BaseData B
    JOIN DistinctRanked D
      ON B.empno = D.empno
     AND B.VAC_FR_SORT = D.VAC_FR_SORT
    LEFT JOIN RecursiveResult R
      ON D.empno = R.empno
     AND D.rn = R.rn
)

SELECT *
FROM FinalResult
ORDER BY empno, VAC_FR_SORT DESC;




