package com.university.soap.service;

import com.university.ejb.service.ResultServiceBean;
import com.university.persistence.entity.Result;

import javax.ejb.EJB;
import javax.jws.WebMethod;
import javax.jws.WebParam;
import javax.jws.WebResult;
import javax.jws.WebService;
import java.util.List;
import java.util.stream.Collectors;

/**
 * JAX-WS SOAP Web Service for Result verification.
 * Allows external systems to verify academic results.
 */
@WebService(name = "ResultVerificationService", serviceName = "ResultVerificationService", portName = "ResultVerificationPort", targetNamespace = "http://soap.university.com/result")
public class ResultVerificationService {

    @EJB
    private ResultServiceBean resultService;

    /**
     * Get all results for a student by student ID.
     */
    @WebMethod(operationName = "getStudentResults")
    @WebResult(name = "results")
    public List<ResultInfo> getStudentResults(@WebParam(name = "studentId") Long studentId) {
        return resultService.getStudentResults(studentId).stream()
                .map(r -> new ResultInfo(
                        r.getResultId(),
                        r.getStudent() != null ? r.getStudent().getFullName() : "",
                        r.getCourse() != null ? r.getCourse().getCourseName() : "",
                        r.getGrade(),
                        r.getMarksObtained(),
                        r.getTotalMarks(),
                        r.getPercentage()))
                .collect(Collectors.toList());
    }

    /**
     * Verify if a student has passed a specific course.
     */
    @WebMethod(operationName = "hasPassedCourse")
    @WebResult(name = "passed")
    public boolean hasPassedCourse(@WebParam(name = "studentId") Long studentId,
            @WebParam(name = "courseId") Long courseId) {
        List<Result> results = resultService.getStudentResults(studentId);
        return results.stream()
                .filter(r -> r.getCourse() != null && r.getCourse().getCourseId().equals(courseId))
                .anyMatch(r -> !r.getGrade().equals("F"));
    }

    /**
     * Get student transcript (all results with grades).
     */
    @WebMethod(operationName = "getTranscript")
    @WebResult(name = "transcript")
    public TranscriptInfo getTranscript(@WebParam(name = "studentId") Long studentId) {
        List<Result> results = resultService.getStudentResults(studentId);
        List<ResultInfo> resultInfos = results.stream()
                .map(r -> new ResultInfo(
                        r.getResultId(),
                        r.getStudent() != null ? r.getStudent().getFullName() : "",
                        r.getCourse() != null ? r.getCourse().getCourseName() : "",
                        r.getGrade(), r.getMarksObtained(), r.getTotalMarks(), r.getPercentage()))
                .collect(Collectors.toList());

        double avgPercentage = results.stream()
                .mapToDouble(Result::getPercentage)
                .average()
                .orElse(0.0);

        return new TranscriptInfo(studentId, resultInfos, avgPercentage, results.size());
    }

    // SOAP Transfer Objects
    public static class ResultInfo {
        public Long resultId;
        public String studentName;
        public String courseName;
        public String grade;
        public Double marksObtained;
        public Double totalMarks;
        public Double percentage;

        public ResultInfo() {
        }

        public ResultInfo(Long resultId, String studentName, String courseName,
                String grade, Double marksObtained, Double totalMarks, Double percentage) {
            this.resultId = resultId;
            this.studentName = studentName;
            this.courseName = courseName;
            this.grade = grade;
            this.marksObtained = marksObtained;
            this.totalMarks = totalMarks;
            this.percentage = percentage;
        }
    }

    public static class TranscriptInfo {
        public Long studentId;
        public List<ResultInfo> results;
        public Double averagePercentage;
        public Integer totalCourses;

        public TranscriptInfo() {
        }

        public TranscriptInfo(Long studentId, List<ResultInfo> results,
                Double averagePercentage, Integer totalCourses) {
            this.studentId = studentId;
            this.results = results;
            this.averagePercentage = averagePercentage;
            this.totalCourses = totalCourses;
        }
    }
}
