package com.university.web.controller;

import com.university.ejb.service.EnrollmentServiceBean;
import com.university.ejb.service.CourseServiceBean;
import com.university.persistence.entity.Course;
import com.university.persistence.entity.Enrollment;

import javax.ejb.EJB;
import javax.enterprise.context.RequestScoped;
import javax.faces.application.FacesMessage;
import javax.faces.context.FacesContext;
import javax.inject.Inject;
import javax.inject.Named;
import java.io.Serializable;
import java.util.List;

/**
 * JSF Managed Bean for Enrollment Management Module.
 */
@Named("enrollmentBean")
@RequestScoped
public class EnrollmentBean implements Serializable {

    @EJB
    private EnrollmentServiceBean enrollmentService;

    @EJB
    private CourseServiceBean courseService;

    @Inject
    private AuthBean authBean;

    // Form fields
    private Long selectedCourseId;
    private String semester;

    private List<Enrollment> enrollments;
    private List<Course> availableCourses;

    /**
     * Enroll the logged-in student in a course.
     */
    public String enrollInCourse() {
        try {
            Long studentId = authBean.getLoggedInUserId();
            enrollmentService.enrollStudent(studentId, selectedCourseId, semester);
            addInfo("Successfully enrolled in course!");
            enrollments = null;
        } catch (IllegalArgumentException e) {
            addError(e.getMessage());
        }
        return null;
    }

    /**
     * Drop an enrollment by ID.
     */
    public String dropCourse(Long enrollmentId) {
        try {
            enrollmentService.dropEnrollment(enrollmentId);
            addInfo("Course dropped successfully.");
            enrollments = null;
        } catch (Exception e) {
            addError("Could not drop course: " + e.getMessage());
        }
        return null;
    }

    /**
     * Get enrollments for the currently logged-in student.
     */
    public List<Enrollment> getMyEnrollments() {
        if (enrollments == null && authBean.isStudent()) {
            enrollments = enrollmentService.getStudentEnrollments(authBean.getLoggedInUserId());
        }
        return enrollments;
    }

    /**
     * Get all enrollments (for admin view).
     */
    public List<Enrollment> getAllEnrollments() {
        if (enrollments == null) {
            enrollments = enrollmentService.getAllEnrollments();
        }
        return enrollments;
    }

    /**
     * Get enrollments for a specific course (faculty view).
     */
    public List<Enrollment> getCourseEnrollments(Long courseId) {
        return enrollmentService.getCourseEnrollments(courseId);
    }

    public List<Course> getAvailableCourses() {
        if (availableCourses == null) {
            availableCourses = courseService.getAllCourses();
        }
        return availableCourses;
    }

    public Long getEnrollmentCount() {
        return enrollmentService.getEnrollmentCount();
    }

    private void addInfo(String msg) {
        FacesContext.getCurrentInstance().addMessage(null,
                new FacesMessage(FacesMessage.SEVERITY_INFO, "Success", msg));
    }

    private void addError(String msg) {
        FacesContext.getCurrentInstance().addMessage(null,
                new FacesMessage(FacesMessage.SEVERITY_ERROR, "Error", msg));
    }

    // Getters and Setters
    public Long getSelectedCourseId() {
        return selectedCourseId;
    }

    public void setSelectedCourseId(Long selectedCourseId) {
        this.selectedCourseId = selectedCourseId;
    }

    public String getSemester() {
        return semester;
    }

    public void setSemester(String semester) {
        this.semester = semester;
    }

    public List<Enrollment> getEnrollments() {
        return enrollments;
    }
}
