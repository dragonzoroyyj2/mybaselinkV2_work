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

