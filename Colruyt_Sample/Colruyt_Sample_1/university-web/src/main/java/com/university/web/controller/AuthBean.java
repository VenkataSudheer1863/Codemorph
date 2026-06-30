package com.university.web.controller;

import com.university.ejb.service.FacultyServiceBean;
import com.university.ejb.service.StudentServiceBean;
import com.university.persistence.entity.Faculty;
import com.university.persistence.entity.Student;

import javax.ejb.EJB;
import javax.enterprise.context.SessionScoped;
import javax.faces.application.FacesMessage;
import javax.faces.context.FacesContext;
import javax.inject.Named;
import java.io.Serializable;
import java.util.Optional;

/**
 * JSF Session-Scoped Managed Bean handling user authentication and session
 * management.
 * Manages login/logout for all roles: ADMIN, FACULTY, STUDENT.
 */
@Named("authBean")
@SessionScoped
public class AuthBean implements Serializable {

    private static final long serialVersionUID = 1L;

    // Hard-coded admin credentials (in production, store in DB)
    private static final String ADMIN_EMAIL = "admin@university.edu";
    private static final String ADMIN_PASSWORD = "Admin@123";

    @EJB
    private StudentServiceBean studentService;

    @EJB
    private FacultyServiceBean facultyService;

    // UI binding fields
    private String email;
    private String password;

    // Session state
    private String loggedInRole; // "ADMIN", "FACULTY", "STUDENT"
    private Long loggedInUserId;
    private String loggedInName;
    private boolean loggedIn = false;

    /**
     * Perform login — checks admin, then faculty, then student credentials.
     */
    public String login() {
        FacesContext context = FacesContext.getCurrentInstance();

        if (email == null || email.trim().isEmpty() || password == null || password.trim().isEmpty()) {
            context.addMessage(null, new FacesMessage(FacesMessage.SEVERITY_ERROR,
                    "Error", "Email and password are required."));
            return null;
        }

        // 1. Check Admin
        if (ADMIN_EMAIL.equalsIgnoreCase(email.trim()) && ADMIN_PASSWORD.equals(password)) {
            setupSession("ADMIN", 0L, "Administrator");
            return "/admin/admin-dashboard?faces-redirect=true";
        }

        // 2. Check Faculty
        Optional<Faculty> faculty = facultyService.authenticate(email.trim(), password);
        if (faculty.isPresent()) {
            setupSession("FACULTY", faculty.get().getFacultyId(), faculty.get().getName());
            return "/faculty/faculty-dashboard?faces-redirect=true";
        }

        // 3. Check Student
        Optional<Student> student = studentService.authenticate(email.trim(), password);
        if (student.isPresent()) {
            setupSession("STUDENT", student.get().getStudentId(), student.get().getFullName());
            return "/student/student-dashboard?faces-redirect=true";
        }

        context.addMessage(null, new FacesMessage(FacesMessage.SEVERITY_ERROR,
                "Login Failed", "Invalid email or password."));
        return null;
    }

    /**
     * Logout — invalidate session and redirect to login.
     */
    public String logout() {
        FacesContext.getCurrentInstance().getExternalContext().invalidateSession();
        return "/login?faces-redirect=true";
    }

    private void setupSession(String role, Long userId, String name) {
        this.loggedInRole = role;
        this.loggedInUserId = userId;
        this.loggedInName = name;
        this.loggedIn = true;
    }

    public boolean isAdmin() {
        return "ADMIN".equals(loggedInRole);
    }

    public boolean isFaculty() {
        return "FACULTY".equals(loggedInRole);
    }

    public boolean isStudent() {
        return "STUDENT".equals(loggedInRole);
    }

    // Getters & Setters
    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getPassword() {
        return password;
    }

    public void setPassword(String password) {
        this.password = password;
    }

    public String getLoggedInRole() {
        return loggedInRole;
    }

    public Long getLoggedInUserId() {
        return loggedInUserId;
    }

    public String getLoggedInName() {
        return loggedInName;
    }

    public boolean isLoggedIn() {
        return loggedIn;
    }
}
