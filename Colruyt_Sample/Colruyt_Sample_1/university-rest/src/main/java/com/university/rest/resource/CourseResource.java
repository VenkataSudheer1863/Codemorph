package com.university.rest.resource;

import com.university.ejb.service.CourseServiceBean;
import com.university.persistence.entity.Course;

import javax.ejb.EJB;
import javax.ws.rs.*;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.Response;
import java.util.List;

/**
 * JAX-RS REST Resource for Course operations.
 */
@Path("/courses")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class CourseResource {

    @EJB
    private CourseServiceBean courseService;

    /**
     * GET /api/courses - Get all courses
     */
    @GET
    public Response getAllCourses() {
        List<Course> courses = courseService.getAllCourses();
        return Response.ok(courses).build();
    }

    /**
     * GET /api/courses/{id} - Get course by ID
     */
    @GET
    @Path("/{id}")
    public Response getCourseById(@PathParam("id") Long id) {
        try {
            Course course = courseService.getCourseById(id);
            return Response.ok(course).build();
        } catch (IllegalArgumentException e) {
            return Response.status(Response.Status.NOT_FOUND)
                    .entity("{\"error\": \"" + e.getMessage() + "\"}")
                    .build();
        }
    }

    /**
     * GET /api/courses/department/{dept} - Get courses by department
     */
    @GET
    @Path("/department/{dept}")
    public Response getCoursesByDepartment(@PathParam("dept") String department) {
        return Response.ok(courseService.getCoursesByDepartment(department)).build();
    }

    /**
     * POST /api/courses - Create a course
     */
    @POST
    public Response createCourse(CourseRequest request) {
        try {
            Course course = courseService.createCourse(
                    request.getCourseName(), request.getCredits(),
                    request.getDepartment(), request.getFacultyId());
            return Response.status(Response.Status.CREATED).entity(course).build();
        } catch (IllegalArgumentException e) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity("{\"error\": \"" + e.getMessage() + "\"}")
                    .build();
        }
    }

    /**
     * PUT /api/courses/{id} - Update a course
     */
    @PUT
    @Path("/{id}")
    public Response updateCourse(@PathParam("id") Long id, CourseRequest request) {
        try {
            Course course = courseService.updateCourse(
                    id, request.getCourseName(), request.getCredits(),
                    request.getDepartment(), request.getFacultyId());
            return Response.ok(course).build();
        } catch (IllegalArgumentException e) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity("{\"error\": \"" + e.getMessage() + "\"}")
                    .build();
        }
    }

    /**
     * DELETE /api/courses/{id} - Delete a course
     */
    @DELETE
    @Path("/{id}")
    public Response deleteCourse(@PathParam("id") Long id) {
        courseService.deleteCourse(id);
        return Response.noContent().build();
    }

    public static class CourseRequest {
        private String courseName;
        private Integer credits;
        private String department;
        private Long facultyId;

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

        public Long getFacultyId() {
            return facultyId;
        }

        public void setFacultyId(Long facultyId) {
            this.facultyId = facultyId;
        }
    }
}
