package com.university.web.controller;

import com.university.ejb.service.CourseServiceBean;
import com.university.ejb.service.FacultyServiceBean;
import com.university.persistence.entity.Course;
import com.university.persistence.entity.Faculty;

import javax.ejb.EJB;
import javax.enterprise.context.RequestScoped;
import javax.faces.application.FacesMessage;
import javax.faces.context.FacesContext;
import javax.inject.Named;
import java.io.Serializable;
import java.util.List;

/**
 * JSF Managed Bean for Course Management Module.
 */
@Named("courseBean")
@RequestScoped
public class CourseBean implements Serializable {

    @EJB
    private CourseServiceBean courseService;

    @EJB
    private FacultyServiceBean facultyService;

    // Form fields
    private Long courseId;
    private String courseName;
    private Integer credits;
    private String department;
    private Long selectedFacultyId;
    private String searchQuery;

    private List<Course> courses;
    private List<Faculty> allFaculty;

    public List<Course> getAllCourses() {
        if (courses == null) {
            courses = courseService.getAllCourses();
        }
        return courses;
    }

    public List<Faculty> getAllFaculty() {
        if (allFaculty == null) {
            allFaculty = facultyService.getAllFaculty();
        }
        return allFaculty;
    }

    public String searchCourses() {
        if (searchQuery != null && !searchQuery.trim().isEmpty()) {
            courses = courseService.searchCourses(searchQuery.trim());
        } else {
            courses = courseService.getAllCourses();
        }
        return null;
    }

    public String editCourse(Long id) {
        try {
            Course c = courseService.getCourseById(id);
            this.courseId = c.getCourseId();
            this.courseName = c.getCourseName();
            this.credits = c.getCredits();
            this.department = c.getDepartment();
            this.selectedFacultyId = c.getFaculty() != null ? c.getFaculty().getFacultyId() : null;
        } catch (Exception e) {
            addError("Could not load course: " + e.getMessage());
        }
        return null;
    }

    public String saveCourse() {
        try {
            courseService.createCourse(courseName, credits, department, selectedFacultyId);
            addInfo("Course created successfully.");
            clearForm();
            courses = null;
        } catch (IllegalArgumentException e) {
            addError(e.getMessage());
        }
        return null;
    }

    public String updateCourse() {
        try {
            courseService.updateCourse(courseId, courseName, credits, department, selectedFacultyId);
            addInfo("Course updated successfully.");
            clearForm();
            courses = null;
        } catch (IllegalArgumentException e) {
            addError(e.getMessage());
        }
        return null;
    }

    public String deleteCourse(Long id) {
        try {
            courseService.deleteCourse(id);
            addInfo("Course deleted successfully.");
            courses = null;
        } catch (Exception e) {
            addError("Could not delete course: " + e.getMessage());
        }
        return null;
    }

    public Long getCourseCount() {
        return courseService.getCourseCount();
    }

    private void clearForm() {
        courseId = null;
        courseName = null;
        credits = null;
        department = null;
        selectedFacultyId = null;
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
    public Long getCourseId() {
        return courseId;
    }

    public void setCourseId(Long courseId) {
        this.courseId = courseId;
    }

    public String getCourseName() {
        return courseName;
    }

    public void setCourseName(String courseName) {
        this.courseName = courseName;
    }

    public Integer getCredits() {
        return credits;
    }

    public void setCredits(Integer credits) {
        this.credits = credits;
    }

    public String getDepartment() {
        return department;
    }

    public void setDepartment(String department) {
        this.department = department;
    }

    public Long getSelectedFacultyId() {
        return selectedFacultyId;
    }

    public void setSelectedFacultyId(Long selectedFacultyId) {
        this.selectedFacultyId = selectedFacultyId;
    }

    public String getSearchQuery() {
        return searchQuery;
    }

    public void setSearchQuery(String searchQuery) {
        this.searchQuery = searchQuery;
    }

    public List<Course> getCourses() {
        return getAllCourses();
    }
}
