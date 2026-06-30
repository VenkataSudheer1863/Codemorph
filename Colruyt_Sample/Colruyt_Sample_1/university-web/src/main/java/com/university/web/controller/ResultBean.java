package com.university.web.controller;

import com.university.ejb.service.ResultServiceBean;
import com.university.ejb.service.CourseServiceBean;
import com.university.ejb.service.StudentServiceBean;
import com.university.persistence.entity.Course;
import com.university.persistence.entity.Result;
import com.university.persistence.entity.Student;

import javax.ejb.EJB;
import javax.enterprise.context.RequestScoped;
import javax.faces.application.FacesMessage;
import javax.faces.context.FacesContext;
import javax.inject.Inject;
import javax.inject.Named;
import java.io.Serializable;
import java.util.List;

/**
 * JSF Managed Bean for Results Management Module.
 */
@Named("resultBean")
@RequestScoped
public class ResultBean implements Serializable {

    @EJB
    private ResultServiceBean resultService;

    @EJB
    private StudentServiceBean studentService;

    @EJB
    private CourseServiceBean courseService;

    @Inject
    private AuthBean authBean;

    // Form fields
    private Long selectedStudentId;
    private Long selectedCourseId;
    private String grade;
    private Double marksObtained;
    private Double totalMarks;
    private String remarks;

    private List<Result> results;
    private List<Student> allStudents;
    private List<Course> allCourses;

    /**
     * Get results for the logged-in student.
     */
    public List<Result> getMyResults() {
        if (results == null && authBean.isStudent()) {
            results = resultService.getStudentResults(authBean.getLoggedInUserId());
        }
        return results;
    }

    /**
     * Get all results (admin view).
     */
    public List<Result> getAllResults() {
        if (results == null) {
            results = resultService.getAllResults();
        }
        return results;
    }

    /**
     * Get results for courses taught by the logged-in faculty.
     */
    public List<Result> getFacultyCourseResults() {
        if (results == null && authBean.isFaculty()) {
            List<Course> myCourses = courseService.getCoursesByFaculty(authBean.getLoggedInUserId());
            if (myCourses != null && !myCourses.isEmpty()) {
                results = resultService.getCourseResults(myCourses.get(0).getCourseId());
            }
        }
        return results;
    }

    public List<Result> getCourseResults(Long courseId) {
        return resultService.getCourseResults(courseId);
    }

    /**
     * Publish a result.
     */
    public String publishResult() {
        try {
            resultService.publishResult(selectedStudentId, selectedCourseId,
                    grade, marksObtained, totalMarks, remarks);
            addInfo("Result published successfully.");
            clearForm();
            results = null;
        } catch (IllegalArgumentException e) {
            addError(e.getMessage());
        }
        return null;
    }

    public String deleteResult(Long id) {
        try {
            resultService.deleteResult(id);
            addInfo("Result deleted.");
            results = null;
        } catch (Exception e) {
            addError("Could not delete result.");
        }
        return null;
    }

    public List<Student> getAllStudents() {
        if (allStudents == null)
            allStudents = studentService.getAllStudents();
        return allStudents;
    }

    public List<Course> getAllCourses() {
        if (allCourses == null)
            allCourses = courseService.getAllCourses();
        return allCourses;
    }

    private void clearForm() {
        selectedStudentId = null;
        selectedCourseId = null;
        grade = null;
        marksObtained = null;
        totalMarks = null;
        remarks = null;
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
    public Long getSelectedStudentId() {
        return selectedStudentId;
    }

    public void setSelectedStudentId(Long selectedStudentId) {
        this.selectedStudentId = selectedStudentId;
    }

    public Long getSelectedCourseId() {
        return selectedCourseId;
    }

    public void setSelectedCourseId(Long selectedCourseId) {
        this.selectedCourseId = selectedCourseId;
    }

    public String getGrade() {
        return grade;
    }

    public void setGrade(String grade) {
        this.grade = grade;
    }

    public Double getMarksObtained() {
        return marksObtained;
    }

    public void setMarksObtained(Double marksObtained) {
        this.marksObtained = marksObtained;
    }

    public Double getTotalMarks() {
        return totalMarks;
    }

    public void setTotalMarks(Double totalMarks) {
        this.totalMarks = totalMarks;
    }

    public String getRemarks() {
        return remarks;
    }

    public void setRemarks(String remarks) {
        this.remarks = remarks;
    }
}
