package com.yourproject.stock;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling; // 👈 이 부분을 추가

@SpringBootApplication
@EnableScheduling // 스케줄링 활성화
public class YourProjectApplication {
    public static void main(String[] args) {
        SpringApplication.run(YourProjectApplication.class, args);
    }
}