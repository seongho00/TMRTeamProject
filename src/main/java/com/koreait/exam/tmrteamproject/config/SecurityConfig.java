package com.koreait.exam.tmrteamproject.config;

import com.koreait.exam.tmrteamproject.service.CustomUserDetailsService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.dao.DaoAuthenticationProvider;
import org.springframework.security.config.annotation.authentication.builders.AuthenticationManagerBuilder;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.AuthenticationFailureHandler;
import org.springframework.security.web.authentication.SimpleUrlAuthenticationFailureHandler;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Autowired
    private CustomUserDetailsService customUserDetailsService;

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
                .authenticationProvider(authenticationProvider(customUserDetailsService, passwordEncoder()))
                .csrf().ignoringAntMatchers("/ws/**").and()
                .authorizeHttpRequests((auth) -> auth
                        .antMatchers("usr/static/**", "usr/images/**", "/css/**", "/static/js/**").permitAll()  // 정적 리소스 먼저 허용
                        .antMatchers("/admin/**").hasRole("ADMIN")
                        .antMatchers("usr/chatbot/chat").hasAnyRole("USER", "ADMIN") // 여기에 막을 url 적기
                        .anyRequest().permitAll()
                )
                .formLogin((login) -> login
                        .loginPage("/usr/member/joinAndLogin") // 사용자 정의 로그인 페이지
                        .loginProcessingUrl("/usr/member/doLogin")
                        .defaultSuccessUrl("/usr/home/main") // 로그인 성공 시 이동
                        .failureHandler(customFailureHandler())  // ✅ 여기가 핵심
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
    public AuthenticationFailureHandler customFailureHandler() {
        return new SimpleUrlAuthenticationFailureHandler() {
            @Override
            public void onAuthenticationFailure(HttpServletRequest request, HttpServletResponse response,
                                                AuthenticationException exception) throws IOException, ServletException {

                String errorMsg = "로그인 실패";

                System.out.println("❗ exception = " + exception.getClass());
                System.out.println("❗ cause = " + exception.getCause());

                if (exception instanceof UsernameNotFoundException) {
                    errorMsg = "가입된 이메일이 없습니다.";
                } else if (exception instanceof BadCredentialsException) {
                    errorMsg = "비밀번호가 틀렸습니다.";
                }

                request.getSession().setAttribute("errorMessage", errorMsg);
                response.sendRedirect("/usr/member/login?error=true");
            }
        };
    }

    @Bean
    public DaoAuthenticationProvider authenticationProvider(UserDetailsService userDetailsService, PasswordEncoder passwordEncoder) {
        DaoAuthenticationProvider authProvider = new DaoAuthenticationProvider();
        authProvider.setUserDetailsService(userDetailsService);
        authProvider.setPasswordEncoder(passwordEncoder);
        authProvider.setHideUserNotFoundExceptions(false); // ✅ 이거 설정해야 UsernameNotFoundException 그대로 던짐
        return authProvider;
    }


    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}
