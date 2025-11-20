  drop table hp040d;
  
CREATE TABLE hp040d (
  yyyy                  VARCHAR2(4),
    entity                VARCHAR2(10),
    empno                 VARCHAR2(20),
    empnm                 VARCHAR2(50),
    biz_section           VARCHAR2(20),
    dept_nm               VARCHAR2(100),
    paycd_nm              VARCHAR2(100),
    paygd1_nm             VARCHAR2(100),
    poscd                 VARCHAR2(20),

    entdt                  VARCHAR2(20),
    retdt                  VARCHAR2(20),

    yy_vac_fr              VARCHAR2(20),
    yy_vac_to              VARCHAR2(20),
    yy_vac_fr_to          VARCHAR2(50),

    vac_list_yy_fr         VARCHAR2(50),
    vac_lit_yy_fr          VARCHAR2(20),

    vac_list_mm_fr        VARCHAR2(10),
    vac_list_mm_to        VARCHAR2(10),

    usable_vac_dd_cnt     NUMBER,
    use_cnt               NUMBER,
    year_use_cnt          NUMBER,
    half_use_cnt          NUMBER,
    half_half_use_cnt     NUMBER,

    tot_yy_vac_dd_cnt     NUMBER,
    yy_vac_dd_cnt         NUMBER,
    yy_vac_dd_cnt_add     NUMBER,
    yy_vac_dd_cnt_adj     NUMBER,
    yy_vac_dd_cnt_sub     NUMBER

  
  
);

  select * from hp040d
  
  
 INSERT INTO hp040d
 (
 
 
  select     '2025'    as   yyyy,                                              -- 연도 정보
            '2022'    as   entity,                   -- 법인 코드
            '2004109'    as   empno,                    -- 사번 (주요 키)
            '유림'    as   empnm,                    -- 성명
            '7'    as   biz_section,              -- 사업부 코드
            '전북지사'    as   dept_nm,         -- 부서명
            '월급직'    as   paycd_nm,        -- 직급명
            '전임 9등급'    as   paygd1_nm,       -- 직위명
            '12'    as   poscd,                    -- 직책 코드
            
            '2020-11-30'    as   entdt,            -- 입사일
            ''    as   retdt,                    -- 퇴사일
            
            -- ----------------------------------------------------
            -- [기간 정보 함수]
            -- ----------------------------------------------------
            '2025-11-30' AS yy_vac_fr,      -- 연차 기간 시작일
            '2026-11-29' AS yy_vac_to,      -- 연차 기간 종료일
             
            '2025-11-30 ~ 2026-11-29' AS yy_vac_fr_to,  -- 연차 기간 정보
            
            '2025-11-30' AS vac_list_yy_fr,
            '2026-11-29' AS vac_lit_yy_fr,
             
            '' AS vac_list_mm_fr,             
            '' AS vac_list_mm_to, 
            
            -- ----------------------------------------------------
            -- [계산 Input: 원본 잔여/사용/지급 정보]
            -- ----------------------------------------------------
            17    as   usable_vac_dd_cnt,  -- 잔여일수 (이월 계산 전 원본)
            -----------------------------------------------------------
            0    as   use_cnt,                          -- 사용일수 합계 (원본)            
            0    as   year_use_cnt,                                         -- 년차 사용
            0    as   half_use_cnt,                                         -- 반차 사용
            0    as   half_half_use_cnt,                                    -- 반반차 사용
   

            17    as   tot_yy_vac_dd_cnt,              -- 지급일수 합계 (원본)
            15    as   yy_vac_dd_cnt,                                        -- 기본 부여 일수
            2    as   yy_vac_dd_cnt_add,                                    -- 근속 가산 일수
            0    as   yy_vac_dd_cnt_adj,                                    -- 조정 일수

            0    as   yy_vac_dd_cnt_sub                                   -- 지급일수 > 차감
            
            -- ----------------------------------------------------
            -- [재귀 핵심 Input] 승인된 이월일수 (hwo45m의 실제 값)
            -- ----------------------------------------------------        
                   
          
            
from dual
union all
  select   
        '2024'    as   yyyy,                                                 -- 연도 정보
            '2022'    as   entity,                   -- 법인 코드
            '2004109'    as   empno,                    -- 사번 (주요 키)
            '유림'    as   empnm,                    -- 성명
            '7'    as   biz_section,              -- 사업부 코드
            '전북지사'    as   dept_nm,         -- 부서명
            '월급직'    as   paycd_nm,        -- 직급명
            '전임 9등급'    as   paygd1_nm,       -- 직위명
            '12'    as   poscd,                    -- 직책 코드
            
            '2020-11-30'    as   entdt,            -- 입사일
            ''    as   retdt,                    -- 퇴사일
            
            -- ----------------------------------------------------
            -- [기간 정보 함수]
            -- ----------------------------------------------------
            '2024-11-30' AS yy_vac_fr,      -- 연차 기간 시작일
            '2025-11-29' AS yy_vac_to,      -- 연차 기간 종료일
             
            '2024-11-30 ~ 2025-11-29' AS yy_vac_fr_to,  -- 연차 기간 정보
         
            '2024-11-30' AS vac_list_yy_fr,
            '2025-11-29' AS vac_lit_yy_fr,
             
            '' AS vac_list_mm_fr,             
            '' AS vac_list_mm_to, 
            
            -- ----------------------------------------------------
            -- [계산 Input: 원본 잔여/사용/지급 정보]
            -- ----------------------------------------------------
            2    as   usable_vac_dd_cnt,  -- 잔여일수 (이월 계산 전 원본)
            ------------------------------------------------------------
            
            14    as    use_cnt,                          -- 사용일수 합계 (원본)
            10    as   year_use_cnt,                                         -- 년차 사용
            4    as   half_use_cnt,                                         -- 반차 사용
            0    as   half_half_use_cnt,                                    -- 반반차 사용
  

            16    as   tot_yy_vac_dd_cnt,              -- 지급일수 합계 (원본)
            15    as   yy_vac_dd_cnt,                                        -- 기본 부여 일수
            1    as   yy_vac_dd_cnt_add,                                    -- 근속 가산 일수
            0    as   yy_vac_dd_cnt_adj,                                    -- 조정 일수

            0    as   yy_vac_dd_cnt_sub                                    -- 지급일수 > 차감
            
            -- ----------------------------------------------------
            -- [재귀 핵심 Input] 승인된 이월일수 (hwo45m의 실제 값)
            -- ----------------------------------------------------
  
            
from dual



union all
  select   
        '2025'    as   yyyy,                                                 -- 연도 정보
            '2022'    as   entity,                   -- 법인 코드
            '22000031'    as   empno,                    -- 사번 (주요 키)
            '김근수'    as   empnm,                    -- 성명
            '1'    as   biz_section,              -- 사업부 코드
            '사업총괄처'    as   dept_nm,         -- 부서명
            '월급직'    as   paycd_nm,        -- 직급명
            '처장 17등급'    as   paygd1_nm,       -- 직위명
            '2'    as   poscd,                    -- 직책 코드
            
            '2022-12-31'    as   entdt,            -- 입사일
            ''    as   retdt,                    -- 퇴사일
            
            -- ----------------------------------------------------
            -- [기간 정보 함수]
            -- ----------------------------------------------------
            '2024-12-31' AS yy_vac_fr,      -- 연차 기간 시작일
            '2025-12-30' AS yy_vac_to,      -- 연차 기간 종료일
             
            '2024-12-31 ~ 2025-12-30' AS yy_vac_fr_to,  -- 연차 기간 정보
         
            '2024-12-31' AS vac_list_yy_fr,
            '2025-12-30' AS vac_lit_yy_fr,
             
            '' AS vac_list_mm_fr,             
            '' AS vac_list_mm_to, 
            
            -- ----------------------------------------------------
            -- [계산 Input: 원본 잔여/사용/지급 정보]
            -- ----------------------------------------------------
            6.25    as   usable_vac_dd_cnt,  -- 잔여일수 (이월 계산 전 원본)
            ------------------------------------------------------------
            
            8.75    as    use_cnt,                          -- 사용일수 합계 (원본)
            5    as   year_use_cnt,                                         -- 년차 사용
            1    as   half_use_cnt,                                         -- 반차 사용
            2.75    as   half_half_use_cnt,                                    -- 반반차 사용
  

            15    as   tot_yy_vac_dd_cnt,              -- 지급일수 합계 (원본)
            15    as   yy_vac_dd_cnt,                                        -- 기본 부여 일수
            1    as   yy_vac_dd_cnt_add,                                    -- 근속 가산 일수
            0    as   yy_vac_dd_cnt_adj,                                    -- 조정 일수

            1.25    as   yy_vac_dd_cnt_sub                                    -- 지급일수 > 차감
            
            -- ----------------------------------------------------
            -- [재귀 핵심 Input] 승인된 이월일수 (hwo45m의 실제 값)
            -- ----------------------------------------------------
  
            
from dual

union all
  select   
        '2024'    as   yyyy,                                                 -- 연도 정보
            '2022'    as   entity,                   -- 법인 코드
            '22000031'    as   empno,                    -- 사번 (주요 키)
            '김근수'    as   empnm,                    -- 성명
            '1'    as   biz_section,              -- 사업부 코드
            '경영관리처'    as   dept_nm,         -- 부서명
            '월급직'    as   paycd_nm,        -- 직급명
            '1급 16단계'    as   paygd1_nm,       -- 직위명
            '2'    as   poscd,                    -- 직책 코드
            
            '2022-12-31'    as   entdt,            -- 입사일
            ''    as   retdt,                    -- 퇴사일
            
            -- ----------------------------------------------------
            -- [기간 정보 함수]
            -- ----------------------------------------------------
            '2024-12-31' AS yy_vac_fr,      -- 연차 기간 시작일
            '2025-12-30' AS yy_vac_to,      -- 연차 기간 종료일
             
            '2024-12-31 ~ 2025-12-30' AS yy_vac_fr_to,  -- 연차 기간 정보
         
            '2024-12-31' AS vac_list_yy_fr,
            '2025-12-30' AS vac_lit_yy_fr,
             
            '' AS vac_list_mm_fr,             
            '' AS vac_list_mm_to, 
            
            -- ----------------------------------------------------
            -- [계산 Input: 원본 잔여/사용/지급 정보]
            -- ----------------------------------------------------
            6.25    as   usable_vac_dd_cnt,  -- 잔여일수 (이월 계산 전 원본)
            ------------------------------------------------------------
            
            8.75    as    use_cnt,                          -- 사용일수 합계 (원본)
            5    as   year_use_cnt,                                         -- 년차 사용
            1    as   half_use_cnt,                                         -- 반차 사용
            2.75    as   half_half_use_cnt,                                    -- 반반차 사용
  

            15    as   tot_yy_vac_dd_cnt,              -- 지급일수 합계 (원본)
            15    as   yy_vac_dd_cnt,                                        -- 기본 부여 일수
            1    as   yy_vac_dd_cnt_add,                                    -- 근속 가산 일수
            0    as   yy_vac_dd_cnt_adj,                                    -- 조정 일수

            1.25    as   yy_vac_dd_cnt_sub                                    -- 지급일수 > 차감
            
            -- ----------------------------------------------------
            -- [재귀 핵심 Input] 승인된 이월일수 (hwo45m의 실제 값)
            -- ----------------------------------------------------
  
            
from dual

union all
  select   
        '2023'    as   yyyy,                                                 -- 연도 정보
            '2022'    as   entity,                   -- 법인 코드
            '22000031'    as   empno,                    -- 사번 (주요 키)
            '김근수'    as   empnm,                    -- 성명
            '1'    as   biz_section,              -- 사업부 코드
            '경영관리처'    as   dept_nm,         -- 부서명
            '월급직'    as   paycd_nm,        -- 직급명
            '1급 16단계'    as   paygd1_nm,       -- 직위명
            '2'    as   poscd,                    -- 직책 코드
            
            '2022-12-31'    as   entdt,            -- 입사일
            ''    as   retdt,                    -- 퇴사일
            
            -- ----------------------------------------------------
            -- [기간 정보 함수]
            -- ----------------------------------------------------
            '2023-01-01' AS yy_vac_fr,      -- 연차 기간 시작일
            '2024-12-30' AS yy_vac_to,      -- 연차 기간 종료일
             
            '2023-01-01 ~ 2024-12-30' AS yy_vac_fr_to,  -- 연차 기간 정보
         
            '2024-12-31' AS vac_list_yy_fr,
            '2025-12-30' AS vac_lit_yy_fr,
             
            '2023-01-01' AS vac_list_mm_fr,             
            '' AS vac_list_mm_to, 
            
            -- ----------------------------------------------------
            -- [계산 Input: 원본 잔여/사용/지급 정보]
            -- ----------------------------------------------------
            -0.25    as   usable_vac_dd_cnt,  -- 잔여일수 (이월 계산 전 원본)
            ------------------------------------------------------------
            
            15.25    as    use_cnt,                          -- 사용일수 합계 (원본)
            10    as   year_use_cnt,                                         -- 년차 사용
            3.5    as   half_use_cnt,                                         -- 반차 사용
            1.75    as   half_half_use_cnt,                                    -- 반반차 사용
  

            15    as   tot_yy_vac_dd_cnt,              -- 지급일수 합계 (원본)
            15    as   yy_vac_dd_cnt,                                        -- 기본 부여 일수
            0    as   yy_vac_dd_cnt_add,                                    -- 근속 가산 일수
            0    as   yy_vac_dd_cnt_adj,                                    -- 조정 일수

            1    as   yy_vac_dd_cnt_sub                                    -- 지급일수 > 차감
            
            -- ----------------------------------------------------
            -- [재귀 핵심 Input] 승인된 이월일수 (hwo45m의 실제 값)
            -- ----------------------------------------------------
  
            
from dual
);

select * from hp040d;

CREATE table hw045m
(
 entity VARCHAR2(4),
 req_empno VARCHAR2(10),
 req_dd_cnt number(5,2), 
occr_date VARCHAR2(10)
    )
;