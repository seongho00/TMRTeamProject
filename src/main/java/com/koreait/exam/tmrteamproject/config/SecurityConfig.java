package com.koreait.exam.tmrteamproject.config;

import com.google.auth.oauth2.GoogleCredentials;
import com.google.firebase.FirebaseApp;
import com.google.firebase.FirebaseOptions;
import com.koreait.exam.tmrteamproject.service.CustomUserDetailsService;
import com.koreait.exam.tmrteamproject.service.MemberService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.config.annotation.authentication.builders.AuthenticationManagerBuilder;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;

import javax.annotation.PostConstruct;
import java.io.IOException;
import java.io.InputStream;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Autowired
    private CustomUserDetailsService customUserDetailsService;

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
                .csrf().disable()
                .authorizeHttpRequests((auth) -> auth
                        .antMatchers("usr/static/**", "usr/images/**", "/css/**", "/js/**").permitAll()  // 정적 리소스 먼저 허용
                        .antMatchers("/admin/**").hasRole("ADMIN")
                        .antMatchers("/usr/home/main").hasAnyRole("USER", "ADMIN") // 여기에 막을 url 적기
                        .anyRequest().permitAll()
                )
                .formLogin((login) -> login
                        .loginPage("/usr/member/joinAndLogin") // 사용자 정의 로그인 페이지
                        .loginProcessingUrl("/usr/member/doLogin")
                        .defaultSuccessUrl("/usr/home/main") // 로그인 성공 시 이동
                        .failureUrl("/member/login?error=true")
                        .permitAll()
                )
                .logout((logout) -> logout
                        .logoutUrl("/usr/member/doLogout")
                        .logoutSuccessUrl("/usr/home/main")
                );

        return http.build();
    }

    @Bean
    public AuthenticationManager authenticationManager(HttpSecurity http) throws Exception {
        return http.getSharedObject(AuthenticationManagerBuilder.class)
                .userDetailsService(customUserDetailsService)
                .passwordEncoder(passwordEncoder())
                .and()
                .build();
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}