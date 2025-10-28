package com.mybaselinkV2.app;

import java.util.Base64;
import java.security.SecureRandom;

public class KeyGenerator {
    public static void main(String[] args) {
        SecureRandom random = new SecureRandom();
        byte[] bytes = new byte[32]; // 32바이트 (256비트)
        random.nextBytes(bytes);
        String base64Key = Base64.getEncoder().encodeToString(bytes);
        System.out.println(base64Key);
    }
}

