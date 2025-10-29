package com.mybaselinkV2.app;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableCaching
@EnableScheduling
public class MyBaseLinkV2Application {

    public static void main(String[] args) {
        SpringApplication.run(MyBaseLinkV2Application.class, args);
    }

}
