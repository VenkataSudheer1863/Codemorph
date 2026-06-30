package com.university.rest;

import javax.ws.rs.ApplicationPath;
import javax.ws.rs.core.Application;

/**
 * JAX-RS Application configuration. Sets the base path for all REST endpoints.
 */
@ApplicationPath("/api")
public class RestApplication extends Application {
    // JAX-RS auto-discovers all @Path annotated classes in the package
}
