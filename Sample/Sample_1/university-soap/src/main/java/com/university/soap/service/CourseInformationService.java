package com.university.soap.service;

import com.university.ejb.service.CourseServiceBean;
import com.university.persistence.entity.Course;

import javax.ejb.EJB;
import javax.jws.WebMethod;
import javax.jws.WebParam;
import javax.jws.WebResult;
import javax.jws.WebService;
import java.util.List;
import java.util.stream.Collectors;

/**
 * JAX-WS SOAP Web Service for Course information.
 * Provides course catalog information to external and legacy systems.
 */
@WebService(name = "CourseInformationService", serviceName = "CourseInformationService", portName = "CourseInformationPort", targetNamespace = "http://soap.university.com/course")
public class CourseInformationService {

    @EJB
    private CourseServiceBean courseService;

    /**
     * Get all available courses.
     */
    @WebMethod(operationName = "getAllCourses")
    @WebResult(name = "courses")
    public List<CourseInfo> getAllCourses() {
        return courseService.getAllCourses().stream()
                .map(c -> new CourseInfo(c.getCourseId(), c.getCourseName(),
                        c.getCredits(), c.getDepartment(), c.getFacultyName()))
                .collect(Collectors.toList());
    }

    /**
     * Get courses offered by a specific department.
     */
    @WebMethod(operationName = "getCoursesByDepartment")
    @WebResult(name = "courses")
    public List<CourseInfo> getCoursesByDepartment(@WebParam(name = "department") String department) {
        return courseService.getCoursesByDepartment(department).stream()
                .map(c -> new CourseInfo(c.getCourseId(), c.getCourseName(),
                        c.getCredits(), c.getDepartment(), c.getFacultyName()))
                .collect(Collectors.toList());
    }

    /**
     * Check if a course exists.
     */
    @WebMethod(operationName = "courseExists")
    @WebResult(name = "exists")
    public boolean courseExists(@WebParam(name = "courseId") Long courseId) {
        try {
            courseService.getCourseById(courseId);
            return true;
        } catch (IllegalArgumentException e) {
            return false;
        }
    }

    /**
     * Get total available courses count.
     */
    @WebMethod(operationName = "getTotalCourseCount")
    @WebResult(name = "count")
    public Long getTotalCourseCount() {
        return courseService.getCourseCount();
    }

    // SOAP Transfer Object
    public static class CourseInfo {
        public Long courseId;
        public String courseName;
        public Integer credits;
        public String department;
        public String facultyName;

        public CourseInfo() {
        }

        public CourseInfo(Long courseId, String courseName, Integer credits,
                String department, String facultyName) {
            this.courseId = courseId;
            this.courseName = courseName;
            this.credits = credits;
            this.department = department;
            this.facultyName = facultyName;
        }
    }
}
