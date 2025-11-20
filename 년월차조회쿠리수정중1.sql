/*
 * [my_select_v2.0] ORA-00904 해결 및 유림/김근수 로직 통합 버전
 * 목적: BaseData에서 YY_VAC_FR을 VAC_FR_SORT로 단순화하여 ORA-00904 오류를 해결하고,
 * hw045m 존재 여부를 기준으로 조건부 재귀 이월을 적용하여 모든 사원에 동일한 로직을 적용합니다.
 */

WITH BaseData AS (
    -- 1. [BaseData] 테이블 조인 및 모든 컬럼에 명시적 별칭 부여
    SELECT
        T.yyyy, T.entity, T.empno, T.empnm, T.dept_nm,
        T.use_cnt, T.tot_yy_vac_dd_cnt, T.usable_vac_dd_cnt,
        
        T.yy_vac_fr AS VAC_FR_SORT, -- ? ORA-00904 오류 회피를 위해 컬럼 이름 단순화 및 고정
        T.dept_nm AS D_NM,          
        
        -- 원본 데이터 컬럼 (최종 SELECT를 위해 유지)
        T.biz_section, T.paycd_nm, T.paygd1_nm, T.poscd, T.entdt, T.retdt, T.yy_vac_to, T.yy_vac_fr_to, 
        T.vac_list_yy_fr, T.vac_list_yy_to, T.vac_list_mm_fr, T.vac_list_mm_to,
        T.year_use_cnt, T.half_use_cnt, T.half_half_use_cnt, T.yy_vac_dd_cnt, T.yy_vac_dd_cnt_add, 
        T.yy_vac_dd_cnt_adj, T.yy_vac_dd_cnt_sub, 
        0 AS req_dd_cnt, 0 AS yy_req_dd_cnt, -- 원본 쿼리에서 0으로 설정된 컬럼
        
        -- hw045m 정보 (이월 신청량)
        NVL(R.req_dd_cnt, 0) AS approved_carryover_dd
        
    FROM hp040d T 
    LEFT JOIN hw045m R ON T.empno = R.req_empno AND T.yy_vac_fr = R.occr_date 
),
RankedData AS (
    -- 1.5. [RankedData] ROW_NUMBER() 계산만을 전담
    SELECT
        B.*, -- BaseData의 모든 컬럼 포함
        
        -- ? 단순화된 별칭을 사용하여 ROW_NUMBER() 계산
        ROW_NUMBER() OVER(PARTITION BY empno ORDER BY VAC_FR_SORT, D_NM) AS rn
        
    FROM BaseData B
),
CleanedVacData AS (
    -- 1.7. [CleanedVacData] 최종 계산을 위한 컬럼 정리 및 로직 통합
    SELECT
        R.yyyy, R.entity, R.empno, R.empnm, R.dept_nm, R.rn, R.approved_carryover_dd,
        R.VAC_FR_SORT, -- 정렬 및 최종 출력을 위해 유지
        
        -- 재귀 계산 로직에 필요한 원본 값 별칭
        R.use_cnt AS original_use_cnt,
        R.tot_yy_vac_dd_cnt AS original_grant_sum,
        R.usable_vac_dd_cnt AS original_remaining_before_calc,
        
        -- 최종 SELECT를 위해 나머지 컬럼 모두 유지
        R.biz_section, R.paycd_nm, R.paygd1_nm, R.poscd, R.entdt, R.retdt, R.yy_vac_to, R.yy_vac_fr_to, 
        R.vac_list_yy_fr, R.vac_list_yy_to, R.vac_list_mm_fr, R.vac_list_mm_to,
        R.year_use_cnt, R.half_use_cnt, R.half_half_use_cnt, R.yy_vac_dd_cnt, R.yy_vac_dd_cnt_add, 
        R.yy_vac_dd_cnt_adj, R.yy_vac_dd_cnt_sub, R.req_dd_cnt, R.yy_req_dd_cnt
        
    FROM RankedData R
),
---
RecursiveResult (
    -- 2. [RecursiveResult] 재귀 결과 컬럼 정의
    yyyy, empno, rn,
    calc_grant_sum, calc_remaining_dd, calc_use_cnt, calc_use_carryover_dd, calc_carryover_grant_dd,
    is_current_carryover_approved -- 현재 로우가 이월 승인된 로우인지 (재귀 조건)
) AS (
    -- 3. [앵커 멤버] 재귀 계산의 시작점 (rn=1)
    SELECT
        I.yyyy, I.empno, I.rn,
        
        I.original_grant_sum AS calc_grant_sum,
        
        -- 33. FINAL_잔여일수: hw045m이 있으면 그 값(1.0)으로 설정, 없으면 (지급 - 사용) (-0.25)
        CASE 
            WHEN I.approved_carryover_dd > 0 THEN I.approved_carryover_dd
            ELSE I.original_grant_sum - I.original_use_cnt
        END AS calc_remaining_dd, 
        
        -- 34. FINAL_사용합계: 지급총액 - 잔여일수
        I.original_grant_sum - 
        (CASE 
            WHEN I.approved_carryover_dd > 0 THEN I.approved_carryover_dd
            ELSE I.original_grant_sum - I.original_use_cnt
        END) AS calc_use_cnt, 

        I.approved_carryover_dd AS calc_use_carryover_dd, -- 35. FINAL_사용이월
        
        0.0 AS calc_carryover_grant_dd, -- 37. FINAL_지급이월 (앵커는 0.0)
        
        (CASE WHEN I.approved_carryover_dd > 0 THEN 1 ELSE 0 END) AS is_current_carryover_approved
    FROM CleanedVacData I WHERE I.rn = 1

    UNION ALL
    
    -- 4. [재귀 멤버] 순차 계산 (hw045m 조건부 재귀 이월)
    SELECT
        I.yyyy, I.empno, I.rn,
        
        -- 36. FINAL_지급합계: 직전 로우가 이월 승인된 경우에만 합산 (유림 2025: 15.0 + 1.0 = 16.0)
        I.original_grant_sum + (CASE WHEN R.is_current_carryover_approved = 1 THEN R.calc_remaining_dd ELSE 0.0 END) AS calc_grant_sum,
        
        -- 33. FINAL_잔여일수: FINAL_지급합계 - 현재 원본 사용
        (I.original_grant_sum + (CASE WHEN R.is_current_carryover_approved = 1 THEN R.calc_remaining_dd ELSE 0.0 END)) - I.original_use_cnt AS calc_remaining_dd,
        
        I.original_use_cnt AS calc_use_cnt, -- 34. FINAL_사용합계 (원본 사용)
        
        I.approved_carryover_dd AS calc_use_carryover_dd, -- 35. FINAL_사용이월
        
        -- 37. FINAL_지급이월: 직전 로우의 이월이 승인된 경우에만 반영 (유림 2025: 1.0)
        (CASE WHEN R.is_current_carryover_approved = 1 THEN R.calc_remaining_dd ELSE 0.0 END) AS calc_carryover_grant_dd,
        
        (CASE WHEN I.approved_carryover_dd > 0 THEN 1 ELSE 0 END) AS is_current_carryover_approved
        
    FROM CleanedVacData I
    INNER JOIN RecursiveResult R ON I.empno = R.empno AND I.rn = R.rn + 1
),
FinalResult AS (
    -- 5. [FinalResult] CleanedVacData와 RecursiveResult를 조인하여 최종 결과값 합산
    SELECT
        I.yyyy, I.entity, I.empno, I.empnm, 
        I.VAC_FR_SORT, -- 정렬 키
        
        -- ----------------------------------------------------
        -- [원본 데이터 컬럼] (최종 SELECT를 위해 모두 포함)
        -- ----------------------------------------------------
        I.biz_section, I.dept_nm, I.paycd_nm, I.paygd1_nm, I.poscd, I.entdt, I.retdt,
        I.yy_vac_to, I.yy_vac_fr_to, I.vac_list_yy_fr, I.vac_list_yy_to, I.vac_list_mm_fr, I.vac_list_mm_to,
        I.original_remaining_before_calc, I.original_use_cnt, I.year_use_cnt, I.half_use_cnt, I.half_half_use_cnt,
        I.req_dd_cnt, I.original_grant_sum, I.yy_vac_dd_cnt, I.yy_vac_dd_cnt_add, I.yy_vac_dd_cnt_adj, 
        I.yy_req_dd_cnt, I.yy_vac_dd_cnt_sub, I.approved_carryover_dd, I.rn,
        
        -- ----------------------------------------------------
        -- [재귀 계산 결과 컬럼] (33번 ~ 37번)
        -- ----------------------------------------------------
        ROUND(R.calc_remaining_dd, 2) AS FINAL_잔여일수,
        ROUND(R.calc_use_cnt, 2) AS FINAL_사용합계,
        ROUND(R.calc_use_carryover_dd, 2) AS FINAL_사용이월,
        ROUND(R.calc_grant_sum, 2) AS FINAL_지급합계,
        ROUND(R.calc_carryover_grant_dd, 2) AS FINAL_지급이월
        
    FROM CleanedVacData I
    LEFT JOIN RecursiveResult R ON I.empno = R.empno AND I.rn = R.rn
)
---
-- 6. 최종 SELECT (모든 컬럼 포함, 고객 지정 순서)
SELECT
      yyyy, entity, empno, empnm, biz_section, dept_nm, paycd_nm, paygd1_nm, poscd, entdt, retdt,
      VAC_FR_SORT AS yy_vac_fr, -- ? 별칭을 yy_vac_fr 이름으로 최종 출력
      yy_vac_to, yy_vac_fr_to, vac_list_yy_fr, vac_list_yy_to, vac_list_mm_fr, vac_list_mm_to,
      original_remaining_before_calc AS usable_vac_dd_cnt, 
      original_use_cnt AS use_cnt, year_use_cnt, half_use_cnt, half_half_use_cnt, 
      original_grant_sum AS tot_yy_vac_dd_cnt, yy_vac_dd_cnt, yy_vac_dd_cnt_add, yy_vac_dd_cnt_adj, 
      yy_vac_dd_cnt_sub, approved_carryover_dd, rn,
      
      FINAL_잔여일수, FINAL_사용합계, FINAL_사용이월, FINAL_지급합계, FINAL_지급이월
FROM FinalResult
ORDER BY empno, VAC_FR_SORT DESC;






  CREATE TABLE "MYBASEUSER"."HW045M" 
   (	"ENTITY" VARCHAR2(4 BYTE), 
	"REQ_EMPNO" VARCHAR2(10 BYTE), 
	"REQ_DD_CNT" NUMBER(5,2), 
	"OCCR_DATE" VARCHAR2(10 BYTE)
   ) SEGMENT CREATION IMMEDIATE 
  PCTFREE 10 PCTUSED 40 INITRANS 1 MAXTRANS 255 
 NOCOMPRESS LOGGING
  STORAGE(INITIAL 65536 NEXT 1048576 MINEXTENTS 1 MAXEXTENTS 2147483645
  PCTINCREASE 0 FREELISTS 1 FREELIST GROUPS 1
  BUFFER_POOL DEFAULT FLASH_CACHE DEFAULT CELL_FLASH_CACHE DEFAULT)
  TABLESPACE "USERS" ;




  CREATE TABLE "MYBASEUSER"."HP040D" 
   (	"YYYY" VARCHAR2(4 BYTE), 
	"ENTITY" VARCHAR2(10 BYTE), 
	"EMPNO" VARCHAR2(20 BYTE), 
	"EMPNM" VARCHAR2(50 BYTE), 
	"BIZ_SECTION" VARCHAR2(20 BYTE), 
	"DEPT_NM" VARCHAR2(100 BYTE), 
	"PAYCD_NM" VARCHAR2(100 BYTE), 
	"PAYGD1_NM" VARCHAR2(100 BYTE), 
	"POSCD" VARCHAR2(20 BYTE), 
	"ENTDT" VARCHAR2(20 BYTE), 
	"RETDT" VARCHAR2(20 BYTE), 
	"YY_VAC_FR" VARCHAR2(20 BYTE), 
	"YY_VAC_TO" VARCHAR2(20 BYTE), 
	"YY_VAC_FR_TO" VARCHAR2(50 BYTE), 
	"VAC_LIST_YY_FR" VARCHAR2(50 BYTE), 
	"VAC_LIST_YY_TO" VARCHAR2(20 BYTE), 
	"VAC_LIST_MM_FR" VARCHAR2(10 BYTE), 
	"VAC_LIST_MM_TO" VARCHAR2(10 BYTE), 
	"USABLE_VAC_DD_CNT" NUMBER, 
	"USE_CNT" NUMBER, 
	"YEAR_USE_CNT" NUMBER, 
	"HALF_USE_CNT" NUMBER, 
	"HALF_HALF_USE_CNT" NUMBER, 
	"TOT_YY_VAC_DD_CNT" NUMBER, 
	"YY_VAC_DD_CNT" NUMBER, 
	"YY_VAC_DD_CNT_ADD" NUMBER, 
	"YY_VAC_DD_CNT_ADJ" NUMBER, 
	"YY_VAC_DD_CNT_SUB" NUMBER
   ) SEGMENT CREATION IMMEDIATE 
  PCTFREE 10 PCTUSED 40 INITRANS 1 MAXTRANS 255 
 NOCOMPRESS LOGGING
  STORAGE(INITIAL 65536 NEXT 1048576 MINEXTENTS 1 MAXEXTENTS 2147483645
  PCTINCREASE 0 FREELISTS 1 FREELIST GROUPS 1
  BUFFER_POOL DEFAULT FLASH_CACHE DEFAULT CELL_FLASH_CACHE DEFAULT)
  TABLESPACE "USERS" ;

2025	2022	2004109	유림	7	전북지사	월급직	전임 9등급	12	2020-11-30		2025-11-16	2026-11-15	2025-11-16 ~ 2026-11-15	2025-11-16	2026-11-15			17	0	0	0	0	17	15	2	0	0	0	2	18	0	0	18	1
2024	2022	2004109	유림	7	전북지사	월급직	전임 9등급	12	2020-11-30		2024-11-16	2025-11-15	2024-11-16 ~ 2025-11-15	2024-11-16	2025-11-15			2	14	10	4	0	16	15	1	0	0	1	1	1	15	1	16	0
2025	2022	22000031	김근수	1	사업총괄처	월급직	처장 17등급	2	2022-12-31		2024-12-31	2025-12-30	2024-12-31 ~ 2025-12-30	2024-12-31	2025-12-30			6.25	8.75	5	1	2.75	15	15	0	0	1.25	0	3	6.25	8.75	0	15	0
2024	2022	22000031	김근수	1	경영관리처	월급직	1급 16단계	2	2022-12-31		2024-12-31	2025-12-30	2024-12-31 ~ 2025-12-30	2024-12-31	2025-12-30			6.25	8.75	5	1	2.75	15	15	0	0	1.25	0	2	6.25	8.75	0	15	0
2023	2022	22000031	김근수	1	경영관리처	월급직	1급 16단계	200	2022-12-31		2023-01-01	2024-12-30	2023-01-01 ~ 2024-12-30	2024-12-31	2025-12-30	2023-01-01		-0.25	15.25	10	3.5	1.75	15	15	0	0	1	0	1	-0.25	15.25	0	15	0


 select * from  hp040d;
YYYY, ENTITY, EMPNO, EMPNM, BIZ_SECTION, DEPT_NM, PAYCD_NM, PAYGD1_NM, POSCD, ENTDT, RETDT, YY_VAC_FR, YY_VAC_TO, YY_VAC_FR_TO, VAC_LIST_YY_FR, VAC_LIST_YY_TO, VAC_LIST_MM_FR, VAC_LIST_MM_TO, USABLE_VAC_DD_CNT, USE_CNT, YEAR_USE_CNT, HALF_USE_CNT, HALF_HALF_USE_CNT, TOT_YY_VAC_DD_CNT, YY_VAC_DD_CNT, YY_VAC_DD_CNT_ADD, YY_VAC_DD_CNT_ADJ, YY_VAC_DD_CNT_SUB
2025	2022	2004109	유림	7	전북지사	월급직	전임 9등급	12	2020-11-30		2025-11-16	2026-11-15	2025-11-16 ~ 2026-11-15	2025-11-16	2026-11-15			17	0	0	0	0	17	15	2	0	0
2024	2022	2004109	유림	7	전북지사	월급직	전임 9등급	12	2020-11-30		2024-11-16	2025-11-15	2024-11-16 ~ 2025-11-15	2024-11-16	2025-11-15			2	14	10	4	0	16	15	1	0	0
2025	2022	22000031	김근수	1	사업총괄처	월급직	처장 17등급	2	2022-12-31		2024-12-31	2025-12-30	2024-12-31 ~ 2025-12-30	2024-12-31	2025-12-30			6.25	8.75	5	1	2.75	15	15	0	0	1.25
2024	2022	22000031	김근수	1	경영관리처	월급직	1급 16단계	2	2022-12-31		2024-12-31	2025-12-30	2024-12-31 ~ 2025-12-30	2024-12-31	2025-12-30			6.25	8.75	5	1	2.75	15	15	0	0	1.25
2023	2022	22000031	김근수	1	경영관리처	월급직	1급 16단계	200	2022-12-31		2023-01-01	2024-12-30	2023-01-01 ~ 2024-12-30	2024-12-31	2025-12-30	2023-01-01		-0.25	15.25	10	3.5	1.75	15	15	0	0	1
  
  select * from  hw045m;
ENTITY, REQ_EMPNO, REQ_DD_CNT, OCCR_DATE
2200	2004109	1	2024-11-16
2200	220000311	5	2023-01-01
  
    
