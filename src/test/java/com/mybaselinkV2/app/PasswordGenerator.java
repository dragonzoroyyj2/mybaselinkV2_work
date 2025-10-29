package com.mybaselinkV2.app;

import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

public class PasswordGenerator {
    public static void main(String[] args) {
        BCryptPasswordEncoder encoder = new BCryptPasswordEncoder();
        String password = "1234";
        String encodedPassword = encoder.encode(password);
        System.out.println("Encoded password for '1234': " + encodedPassword);
    }
}

