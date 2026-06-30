package com.university.web.controller;

import com.university.ejb.service.ExamServiceBean;
import com.university.ejb.service.CourseServiceBean;
import com.university.persistence.entity.Course;
import com.university.persistence.entity.Exam;

import javax.ejb.EJB;
import javax.enterprise.context.RequestScoped;
import javax.faces.application.FacesMessage;
import javax.faces.context.FacesContext;
import javax.inject.Inject;
import javax.inject.Named;
import java.io.Serializable;
import java.time.LocalDate;
import java.util.List;

/**
 * JSF Managed Bean for Exam Management Module.
 */
@Named("examBean")
@RequestScoped
public class ExamBean implements Serializable {

    @EJB
    private ExamServiceBean examService;

    @EJB
    private CourseServiceBean courseService;

    @Inject
    private AuthBean authBean;

    // Form fields
    private Long examId;
    private Long selectedCourseId;
    private LocalDate examDate;
    private String examType;
    private String location;
    private Integer durationMinutes;

    private List<Exam> exams;
    private List<Course> courses;

    public List<Exam> getAllExams() {
        if (exams == null) {
            exams = examService.getAllExams();
        }
        return exams;
    }

    public List<Exam> getUpcomingExams() {
        return examService.getUpcomingExams();
    }

    public List<Course> getAllCourses() {
        if (courses == null) {
            if (authBean.isFaculty()) {
                courses = courseService.getCoursesByFaculty(authBean.getLoggedInUserId());
            } else {
                courses = courseService.getAllCourses();
            }
        }
        return courses;
    }

    public String saveExam() {
        try {
            examService.createExam(selectedCourseId, examDate, examType, location, durationMinutes);
            addInfo("Exam scheduled successfully.");
            clearForm();
            exams = null;
        } catch (IllegalArgumentException e) {
            addError(e.getMessage());
        }
        return null;
    }

    public String updateExam() {
        try {
            examService.updateExam(examId, examDate, examType, location, durationMinutes);
            addInfo("Exam updated successfully.");
            clearForm();
            exams = null;
        } catch (IllegalArgumentException e) {
            addError(e.getMessage());
        }
        return null;
    }

    public String deleteExam(Long id) {
        try {
            examService.deleteExam(id);
            addInfo("Exam deleted.");
            exams = null;
        } catch (Exception e) {
            addError("Could not delete exam.");
        }
        return null;
    }

    public String editExam(Long id) {
        try {
            Exam e = examService.getExamById(id);
            this.examId = e.getExamId();
            this.selectedCourseId = e.getCourse().getCourseId();
            this.examDate = e.getExamDate();
            this.examType = e.getExamType();
            this.location = e.getLocation();
            this.durationMinutes = e.getDurationMinutes();
        } catch (Exception e) {
            addError("Could not load exam.");
        }
        return null;
    }

    private void clearForm() {
        examId = null;
        selectedCourseId = null;
        examDate = null;
        examType = null;
        location = null;
        durationMinutes = null;
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
    public Long getExamId() {
        return examId;
    }

    public void setExamId(Long examId) {
        this.examId = examId;
    }

    public Long getSelectedCourseId() {
        return selectedCourseId;
    }

    public void setSelectedCourseId(Long selectedCourseId) {
        this.selectedCourseId = selectedCourseId;
    }

    public LocalDate getExamDate() {
        return examDate;
    }

    public void setExamDate(LocalDate examDate) {
        this.examDate = examDate;
    }

    public String getExamType() {
        return examType;
    }

    public void setExamType(String examType) {
        this.examType = examType;
    }

    public String getLocation() {
        return location;
    }

    public void setLocation(String location) {
        this.location = location;
    }

    public Integer getDurationMinutes() {
        return durationMinutes;
    }

    public void setDurationMinutes(Integer durationMinutes) {
        this.durationMinutes = durationMinutes;
    }

    public List<Exam> getExams() {
        return getAllExams();
    }
}
