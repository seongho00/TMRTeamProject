package com.koreait.exam.tmrteamproject.config;

import com.koreait.exam.tmrteamproject.service.CustomUserDetailsService;
import lombok.extern.slf4j.Slf4j;
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
import org.springframework.security.web.authentication.AuthenticationSuccessHandler;
import org.springframework.security.web.authentication.SimpleUrlAuthenticationFailureHandler;
import org.springframework.security.web.savedrequest.HttpSessionRequestCache;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;

@Configuration
@EnableWebSecurity
@Slf4j
public class SecurityConfig {

    @Autowired
    private CustomUserDetailsService customUserDetailsService;

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
                .authenticationProvider(authenticationProvider(customUserDetailsService, passwordEncoder()))
                .csrf().disable()
                .authorizeHttpRequests((auth) -> auth
                        .antMatchers("/usr/static/**", "/usr/images/**", "/css/**", "/static/js/**").permitAll()  // 정적 리소스 먼저 허용
                        .antMatchers("/admin/**").hasRole("ADMIN")
                        .antMatchers("/usr/chatbot/chat").hasAnyRole("USER", "ADMIN")
                        .antMatchers("/usr/home/notifications").hasAnyRole("USER", "ADMIN")
                        .antMatchers( // 여기에 막을 URL 적기
                                "/usr/member/conditionalLogout",
                                "/usr/member/myPage",
                                "/usr/member/checkPw"
                        ).authenticated()
                        .anyRequest().permitAll()
                )
                .exceptionHandling(ex -> ex
                        .authenticationEntryPoint((request, response, authException) -> {
                            // 로그인 안 했는데 보호된 url 접근시
                            response.setContentType("text/html;charset=UTF-8");
                            response.getWriter().write(
                                    "<script>alert('로그인이 필요한 서비스 입니다.');" +
                                        "location.href='/usr/member/joinAndLogin';</script>"
                            );
                        })
                )
                .formLogin((login) -> login
                        .loginPage("/usr/member/joinAndLogin") // 사용자 정의 로그인 페이지
                        .loginProcessingUrl("/usr/member/doLogin")
                        .successHandler(loginSuccessHandler()) // 성공 핸들러
                        .failureHandler(customFailureHandler())  // 여기가 핵심
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

                System.out.println("exception = " + exception.getClass());
                System.out.println("cause = " + exception.getCause());

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
        authProvider.setHideUserNotFoundExceptions(false); // 이거 설정해야 UsernameNotFoundException 그대로 던짐
        return authProvider;
    }


    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    // 로그인 성공 핸들러
    @Bean
    public AuthenticationSuccessHandler loginSuccessHandler() {

        return (request, response, authentication) -> {
            System.out.println("로그인 여부 : 로그인 되었습니다.");
            log.info("로그인 되었습니다!");

            var cache = new HttpSessionRequestCache();
            var saved = cache.getRequest(request, response);

            if (saved != null) {
                response.sendRedirect(saved.getRedirectUrl());
            } else {
                response.sendRedirect("/usr/home/main");
            }
        };
    }
}
