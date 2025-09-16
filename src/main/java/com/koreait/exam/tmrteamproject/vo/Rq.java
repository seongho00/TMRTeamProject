package com.koreait.exam.tmrteamproject.vo;

import com.koreait.exam.tmrteamproject.security.MemberContext;
import com.koreait.exam.tmrteamproject.util.Ut;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

import org.springframework.context.annotation.Scope;
import org.springframework.context.annotation.ScopedProxyMode;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;

import java.io.IOException;

@Component
@Scope(value = "request", proxyMode = ScopedProxyMode.TARGET_CLASS)
public class Rq {

    private final HttpServletRequest req;
    private final HttpServletResponse resp;
    private final HttpSession session;

    public Rq(HttpServletRequest req, HttpServletResponse resp) {
        this.req = req;
        this.resp = resp;
        this.session = req.getSession();

        this.req.setAttribute("rq", this);
    }

    public void printHistoryBack(String msg) throws IOException {
        resp.setContentType("text/html; charset=UTF-8");
        println("<script>");
        if (!Ut.isEmpty(msg)) {
            println("alert('" + msg.replace("'", "\\'") + "');");
        }
        println("history.back();");
        println("</script>");
        resp.getWriter().flush();
        resp.getWriter().close();
    }

    private void println(String str) throws IOException {
        print(str + "\n");
    }

    private void print(String str) throws IOException {
        resp.getWriter().append(str);
    }

    // 로그인 여부
    public boolean isLogined() {
        return getMemberContext() != null;
    }

    public boolean isLogout() {
        return !isLogined();
    }

    // 로그인된 회원 객체
    public Member getLoginedMember() {
        MemberContext mc = getMemberContext();
        return mc != null ? mc.getMember() : null;
    }

    // 로그인된 회원 ID
    public Long getLoginedMemberId() {
        Member m = getLoginedMember();
        return m != null ? m.getId() : null;
    }

    public MemberContext getMemberContext() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth == null || !auth.isAuthenticated()) return null;

        if (auth.getPrincipal() instanceof MemberContext mc) {
            return mc;
        }

        return null;
    }

    public String historyBackOnView(String msg) {
        req.setAttribute("msg", msg);
        req.setAttribute("historyBack", true);
        req.removeAttribute("replace");

        return "usr/common/js";
    }

    public String replace(String msg, String replaceLocation) {
        req.setAttribute("replaceLocation", replaceLocation);
        req.setAttribute("msg", msg);
        req.setAttribute("replace", true);
        req.removeAttribute("historyBack");
        return "usr/common/js";
    }

    public String getCurrentUri() {
        String currentUri = req.getRequestURI();
        String queryString = req.getQueryString();

        System.out.println(currentUri);
        System.out.println(queryString);

        if (currentUri != null && queryString != null) {
            currentUri += "?" + queryString;
        }

        return currentUri;
    }
}
