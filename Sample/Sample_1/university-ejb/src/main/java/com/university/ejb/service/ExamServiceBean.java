package com.university.ejb.service;

import com.university.persistence.entity.Course;
import com.university.persistence.entity.Exam;
import com.university.persistence.repository.CourseRepository;
import com.university.persistence.repository.ExamRepository;

import javax.ejb.Stateless;
import javax.ejb.TransactionAttribute;
import javax.ejb.TransactionAttributeType;
import javax.inject.Inject;
import java.time.LocalDate;
import java.util.List;

/**
 * Stateless EJB Service Bean for Exam management business logic.
 */
@Stateless
@TransactionAttribute(TransactionAttributeType.REQUIRED)
public class ExamServiceBean {

    @Inject
    private ExamRepository examRepository;

    @Inject
    private CourseRepository courseRepository;

    /**
     * Create an exam schedule for a course.
     */
    public Exam createExam(Long courseId, LocalDate examDate, String examType,
            String location, Integer durationMinutes) {
        Course course = courseRepository.findById(courseId);
        if (course == null)
            throw new IllegalArgumentException("Course not found.");
        if (examDate == null)
            throw new IllegalArgumentException("Exam date is required.");
        if (examDate.isBefore(LocalDate.now()))
            throw new IllegalArgumentException("Exam date cannot be in the past.");

        Exam exam = new Exam(course, examDate, examType, location, durationMinutes);
        return examRepository.save(exam);
    }

    /**
     * Update exam details.
     */
    public Exam updateExam(Long examId, LocalDate examDate, String examType,
            String location, Integer durationMinutes) {
        Exam exam = getExamById(examId);
        exam.setExamDate(examDate);
        exam.setExamType(examType);
        exam.setLocation(location);
        exam.setDurationMinutes(durationMinutes);
        return examRepository.update(exam);
    }

    /**
     * Delete an exam.
     */
    public void deleteExam(Long examId) {
        examRepository.delete(examId);
    }

    /**
     * Get exam by ID.
     */
    @TransactionAttribute(TransactionAttributeType.SUPPORTS)
    public Exam getExamById(Long examId) {
        Exam exam = examRepository.findById(examId);
        if (exam == null)
            throw new IllegalArgumentException("Exam with ID " + examId + " not found.");
        return exam;
    }

    /**
     * Get all exams.
     */
    @TransactionAttribute(TransactionAttributeType.SUPPORTS)
    public List<Exam> getAllExams() {
        return examRepository.findAll();
    }

    /**
     * Get exams by course.
     */
    @TransactionAttribute(TransactionAttributeType.SUPPORTS)
    public List<Exam> getExamsByCourse(Long courseId) {
        return examRepository.findByCourse(courseId);
    }

    /**
     * Get upcoming exams (today and future).
     */
    @TransactionAttribute(TransactionAttributeType.SUPPORTS)
    public List<Exam> getUpcomingExams() {
        return examRepository.findUpcoming();
    }
}
