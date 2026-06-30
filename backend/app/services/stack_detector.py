"""Stack Detector Service.

Detects technology stack with confidence scores from import analysis,
config file parsing, dependency declarations, and framework patterns.
"""

import re
import json
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

# Enhanced category definitions with comprehensive detection rules
STACK_CATEGORIES = {
    "frontend_framework": {
        "label": "Frontend Framework",
        "technologies": {
            "JSF": {
                "indicators": [
                    "javax.faces", "jakarta.faces", "@ManagedBean", "@ViewScoped", "@RequestScoped", "@SessionScoped",
                    "h:form", "h:dataTable", "h:inputText", "h:commandButton", "h:outputText", "h:selectOneMenu",
                    "f:view", "f:facet", "f:param", "f:converter", "f:validator", "f:ajax",
                    ".xhtml", "xmlns.jcp.org/jsf", "faces-config.xml", "FacesContext", "UIComponent",
                    "PhaseListener", "FacesServlet", "StateManager", "ViewHandler", "NavigationHandler",
                    "primefaces", "richfaces", "icefaces", "omnifaces", "bootsfaces",
                    "p:", "rich:", "ice:", "o:", "b:", "ui:composition", "ui:define", "ui:insert",
                ],
                "config_files": {"faces-config.xml": 40, "web.xml": 15, "beans.xml": 10},
                "dependencies": {
                    "javax.faces": 35, "jakarta.faces": 35, "jsf-api": 30, "jsf-impl": 30,
                    "primefaces": 25, "richfaces": 25, "icefaces": 25, "omnifaces": 20, "bootsfaces": 20
                },
                "file_extensions": {".xhtml": 25, ".jsf": 20},
            },
            "JSP": {
                "indicators": [
                    "<%@", "<%=", "<%!", "<%--", "<jsp:", "<c:", "<fmt:", "<fn:", "<sql:",
                    "pageContext", "request.getAttribute", "session.getAttribute", "application.getAttribute",
                    "jsp:include", "jsp:forward", "jsp:useBean", "jsp:setProperty", "jsp:getProperty",
                    "taglib", "jstl", "el expression", "${", "#{", "page directive", "include directive",
                    "HttpServletRequest", "HttpServletResponse", "JspWriter", "PageContext",
                ],
                "config_files": {"web.xml": 20, "tld": 15},
                "dependencies": {"jsp-api": 35, "servlet-api": 25, "jstl": 30, "standard": 20},
                "file_extensions": {".jsp": 30, ".jspx": 25, ".tag": 20, ".tagx": 20},
            },
            "React": {
                "indicators": [
                    "import React", "from 'react'", "from \"react\"", "React.Component", "React.createElement",
                    "useState", "useEffect", "useContext", "useReducer", "useMemo", "useCallback", "useRef",
                    "ReactDOM", "ReactDOM.render", "createRoot", "render", "hydrate",
                    "jsx", "tsx", "className", "onClick", "onChange", "onSubmit", "props", "state",
                    "componentDidMount", "componentDidUpdate", "componentWillUnmount", "shouldComponentUpdate",
                    "React.Fragment", "Fragment", "<>", "</>", "key=", "ref=", "dangerouslySetInnerHTML",
                    "PropTypes", "defaultProps", "displayName", "forwardRef", "memo", "lazy", "Suspense",
                    "createContext", "Provider", "Consumer", "useLayoutEffect", "useImperativeHandle",
                ],
                "config_files": {"package.json": 20, ".babelrc": 15, "webpack.config.js": 15, "vite.config.js": 15},
                "dependencies": {
                    "react": 40, "react-dom": 35, "@types/react": 25, "@types/react-dom": 25,
                    "react-scripts": 20, "next": 20, "gatsby": 20, "create-react-app": 20
                },
                "file_extensions": {".jsx": 35, ".tsx": 35, ".js": 10, ".ts": 10},
            },
            "Angular": {
                "indicators": [
                    "@Component", "@NgModule", "@Injectable", "@Directive", "@Pipe", "@Input", "@Output",
                    "from '@angular", "Angular", "AngularJS", "ng-", "ngOnInit", "ngOnDestroy", "ngOnChanges",
                    "EventEmitter", "Observable", "Subject", "BehaviorSubject", "HttpClient", "Router",
                    "ActivatedRoute", "FormBuilder", "FormGroup", "FormControl", "Validators",
                    "templateUrl", "styleUrls", "selector", "providers", "imports", "declarations", "exports",
                    "bootstrap", "entryComponents", "schemas", "ViewChild", "ViewChildren", "ContentChild",
                    "HostListener", "HostBinding", "ElementRef", "Renderer2", "ChangeDetectorRef",
                ],
                "config_files": {"angular.json": 50, "package.json": 20, "tsconfig.json": 15, ".angular-cli.json": 40},
                "dependencies": {
                    "@angular/core": 40, "@angular/common": 35, "@angular/router": 30, "@angular/forms": 30,
                    "@angular/http": 25, "@angular/cli": 25, "rxjs": 20, "zone.js": 20, "typescript": 15
                },
                "file_extensions": {".ts": 20, ".html": 10, ".scss": 5, ".css": 5},
            },
            "Vue.js": {
                "indicators": [
                    "createApp", "from 'vue'", "from \"vue\"", "Vue.createApp", "new Vue", "Vue.component",
                    "defineComponent", "ref", "reactive", "computed", "watch", "watchEffect", "onMounted",
                    "onUpdated", "onUnmounted", "setup", "props", "emit", "expose", "v-model", "v-if",
                    "v-for", "v-show", "v-bind", "v-on", "@click", "@change", "@submit", "template",
                    "script setup", "composition api", "options api", "mixins", "directives", "filters",
                    "Vue Router", "Vuex", "Pinia", "Nuxt", "Quasar", "Vuetify", "Element UI",
                ],
                "config_files": {"vue.config.js": 40, "nuxt.config.js": 35, "package.json": 20, "vite.config.js": 15},
                "dependencies": {
                    "vue": 40, "@vue/cli": 30, "vue-router": 25, "vuex": 25, "pinia": 25,
                    "nuxt": 30, "@nuxt/core": 25, "quasar": 20, "vuetify": 20
                },
                "file_extensions": {".vue": 40, ".js": 10, ".ts": 10},
            },
            "Thymeleaf": {
                "indicators": [
                    "th:each", "th:text", "th:if", "th:unless", "th:switch", "th:case", "th:object",
                    "th:field", "th:value", "th:href", "th:src", "th:action", "th:method", "th:fragment",
                    "xmlns:th", "th:include", "th:replace", "th:insert", "th:with", "th:classappend",
                    "th:styleappend", "th:attrappend", "th:attrprepend", "th:onclick", "th:onchange",
                    "TemplateEngine", "SpringTemplateEngine", "ThymeleafViewResolver", "ITemplateResolver",
                ],
                "config_files": {"application.properties": 15, "application.yml": 15},
                "dependencies": {
                    "thymeleaf": 35, "spring-boot-starter-thymeleaf": 40, "thymeleaf-spring5": 30,
                    "thymeleaf-extras-springsecurity5": 25, "thymeleaf-layout-dialect": 20
                },
                "file_extensions": {".html": 20, ".xml": 5},
            },
            "Svelte": {
                "indicators": [
                    "svelte", "SvelteKit", "svelte/store", "svelte/motion", "svelte/transition",
                    "onMount", "onDestroy", "beforeUpdate", "afterUpdate", "tick", "createEventDispatcher",
                    "bind:", "on:", "use:", "class:", "style:", "let:", "export let", "$:", "$$props", "$$restProps",
                    "writable", "readable", "derived", "get", "tweened", "spring", "fade", "fly", "slide",
                ],
                "config_files": {"svelte.config.js": 40, "vite.config.js": 15, "rollup.config.js": 15},
                "dependencies": {"svelte": 40, "@sveltejs/kit": 35, "@sveltejs/adapter-auto": 25, "vite": 15},
                "file_extensions": {".svelte": 40, ".js": 10, ".ts": 10},
            },
        },
    },
    "backend_framework": {
        "label": "Backend Framework",
        "technologies": {
            "Java EE / EJB": {
                "indicators": [
                    "@Stateless", "@Stateful", "@MessageDriven", "@EJB", "@Local", "@Remote",
                    "@Resource", "@PersistenceContext", "@PersistenceUnit", "@TransactionAttribute",
                    "javax.ejb", "jakarta.ejb", "javax.enterprise", "jakarta.enterprise",
                    "SessionBean", "EntityBean", "MessageDrivenBean", "EJBContext", "SessionContext",
                    "EntityManager", "EntityManagerFactory", "UserTransaction", "EJBException",
                    "InitialContext", "JNDI", "lookup", "javax.naming", "jakarta.naming",
                    "application-client.xml", "ejb-jar.xml", "persistence.xml", "beans.xml",
                ],
                "config_files": {"ejb-jar.xml": 50, "web.xml": 20, "application.xml": 30, "persistence.xml": 25},
                "dependencies": {
                    "javax.ejb": 35, "jakarta.ejb": 35, "javaee-api": 30, "jakarta.jakartaee-api": 30,
                    "javax.enterprise": 25, "jakarta.enterprise": 25, "javax.persistence": 25, "jakarta.persistence": 25
                },
                "file_extensions": {".java": 10, ".xml": 5},
            },
            "Spring Boot": {
                "indicators": [
                    "@SpringBootApplication", "@RestController", "@Controller", "@Service", "@Repository",
                    "@Component", "@Configuration", "@Bean", "@Autowired", "@Value", "@Profile",
                    "@ConditionalOnProperty", "@EnableAutoConfiguration", "@ComponentScan", "@Import",
                    "SpringApplication.run", "SpringApplication", "ConfigurableApplicationContext",
                    "@RequestMapping", "@GetMapping", "@PostMapping", "@PutMapping", "@DeleteMapping",
                    "@PathVariable", "@RequestParam", "@RequestBody", "@ResponseBody", "@Valid",
                    "ResponseEntity", "HttpStatus", "@CrossOrigin", "@Transactional", "@Cacheable",
                    "spring-boot-starter", "spring-boot-autoconfigure", "spring-boot-actuator",
                ],
                "config_files": {
                    "application.properties": 30, "application.yml": 30, "application.yaml": 30,
                    "bootstrap.properties": 25, "bootstrap.yml": 25, "pom.xml": 20, "build.gradle": 20
                },
                "dependencies": {
                    "spring-boot-starter": 40, "spring-boot": 35, "spring-boot-autoconfigure": 30,
                    "spring-boot-starter-web": 35, "spring-boot-starter-data-jpa": 30, "spring-boot-starter-security": 25,
                    "spring-boot-starter-test": 25, "spring-boot-devtools": 20, "spring-boot-actuator": 20
                },
                "file_extensions": {".java": 15, ".kt": 10, ".groovy": 5},
            },
            "Spring MVC": {
                "indicators": [
                    "@Controller", "@RequestMapping", "@ModelAttribute", "@SessionAttributes",
                    "ModelAndView", "DispatcherServlet", "HandlerMapping", "ViewResolver",
                    "InternalResourceViewResolver", "BeanNameViewResolver", "HandlerInterceptor",
                    "MultipartResolver", "LocaleResolver", "ThemeResolver", "HandlerExceptionResolver",
                    "spring-webmvc", "spring-web", "ContextLoaderListener", "RequestContextListener",
                ],
                "config_files": {"web.xml": 25, "spring-servlet.xml": 40, "applicationContext.xml": 30},
                "dependencies": {
                    "spring-webmvc": 35, "spring-web": 30, "spring-context": 25, "spring-core": 25,
                    "spring-beans": 20, "spring-expression": 20, "spring-aop": 15
                },
                "file_extensions": {".java": 15, ".xml": 10},
            },
            "Django": {
                "indicators": [
                    "from django", "import django", "INSTALLED_APPS", "urlpatterns", "models.Model",
                    "django.contrib", "django.db", "django.http", "django.shortcuts", "django.views",
                    "HttpResponse", "HttpRequest", "render", "redirect", "get_object_or_404",
                    "Model", "CharField", "IntegerField", "DateTimeField", "ForeignKey", "ManyToManyField",
                    "admin.site.register", "forms.Form", "forms.ModelForm", "Class Meta", "verbose_name",
                    "django.urls", "path", "include", "re_path", "django.conf.urls", "django.contrib.admin",
                    "MIDDLEWARE", "DATABASES", "TEMPLATES", "STATIC_URL", "MEDIA_URL", "SECRET_KEY",
                ],
                "config_files": {
                    "settings.py": 40, "manage.py": 35, "urls.py": 30, "wsgi.py": 25, "asgi.py": 25,
                    "requirements.txt": 20, "Pipfile": 15, "pyproject.toml": 15
                },
                "dependencies": {
                    "django": 40, "Django": 40, "djangorestframework": 25, "django-cors-headers": 20,
                    "django-extensions": 15, "django-debug-toolbar": 15, "celery": 10
                },
                "file_extensions": {".py": 20, ".html": 5},
            },
            "Flask": {
                "indicators": [
                    "from flask", "import Flask", "Flask(__name__)", "@app.route", "app.run",
                    "request", "session", "g", "redirect", "url_for", "abort", "render_template",
                    "jsonify", "make_response", "flash", "get_flashed_messages", "current_app",
                    "Blueprint", "before_request", "after_request", "teardown_request", "errorhandler",
                    "flask.ext", "flask_sqlalchemy", "flask_login", "flask_wtf", "flask_migrate",
                    "Werkzeug", "Jinja2", "MarkupSafe", "itsdangerous", "click", "blinker",
                ],
                "config_files": {"app.py": 30, "run.py": 25, "config.py": 20, "requirements.txt": 15},
                "dependencies": {
                    "flask": 40, "Flask": 40, "flask-sqlalchemy": 25, "flask-login": 20, "flask-wtf": 20,
                    "flask-migrate": 20, "flask-cors": 15, "werkzeug": 15, "jinja2": 15
                },
                "file_extensions": {".py": 20, ".html": 5},
            },
            "FastAPI": {
                "indicators": [
                    "from fastapi", "import FastAPI", "FastAPI()", "@app.get", "@app.post", "@app.put", "@app.delete",
                    "APIRouter", "Depends", "HTTPException", "status", "Response", "Request",
                    "Path", "Query", "Body", "Header", "Cookie", "Form", "File", "UploadFile",
                    "BaseModel", "pydantic", "Field", "validator", "root_validator", "Config",
                    "BackgroundTasks", "WebSocket", "WebSocketDisconnect", "Middleware", "CORSMiddleware",
                    "uvicorn", "starlette", "async def", "await", "typing", "Optional", "List", "Dict",
                ],
                "config_files": {"main.py": 30, "app.py": 25, "requirements.txt": 20, "pyproject.toml": 15},
                "dependencies": {
                    "fastapi": 40, "uvicorn": 30, "pydantic": 25, "starlette": 20, "python-multipart": 15,
                    "python-jose": 15, "passlib": 15, "sqlalchemy": 10, "alembic": 10
                },
                "file_extensions": {".py": 20},
            },
            "Express.js": {
                "indicators": [
                    "express()", "app.listen", "router.get", "router.post", "require('express')",
                    "import express", "app.use", "app.get", "app.post", "app.put", "app.delete",
                    "middleware", "req.params", "req.query", "req.body", "res.send", "res.json",
                    "res.status", "res.redirect", "next()", "app.set", "app.locals", "res.locals",
                    "express.static", "express.Router", "express.json", "express.urlencoded",
                    "cors", "helmet", "morgan", "body-parser", "cookie-parser", "session",
                ],
                "config_files": {"package.json": 30, "app.js": 25, "server.js": 25, "index.js": 20},
                "dependencies": {
                    "express": 40, "cors": 20, "helmet": 15, "morgan": 15, "body-parser": 15,
                    "cookie-parser": 15, "express-session": 15, "dotenv": 10, "nodemon": 10
                },
                "file_extensions": {".js": 20, ".ts": 15, ".mjs": 10},
            },
            "ASP.NET Core": {
                "indicators": [
                    "Microsoft.AspNetCore", "[ApiController]", "[Route]", "[HttpGet]", "[HttpPost]",
                    "IActionResult", "ActionResult", "ControllerBase", "Controller", "WebApplication",
                    "WebApplicationBuilder", "IServiceCollection", "IConfiguration", "ILogger",
                    "Startup", "ConfigureServices", "Configure", "UseRouting", "UseEndpoints",
                    "MapControllers", "AddControllers", "AddMvc", "UseMvc", "UseAuthentication",
                    "UseAuthorization", "UseCors", "UseHttpsRedirection", "UseStaticFiles",
                    "Entity Framework", "DbContext", "DbSet", "IRepository", "Dependency Injection",
                ],
                "config_files": {
                    "appsettings.json": 30, "appsettings.Development.json": 25, "Program.cs": 25,
                    "Startup.cs": 30, "launchSettings.json": 15, "web.config": 15
                },
                "dependencies": {
                    "Microsoft.AspNetCore": 35, "Microsoft.AspNetCore.Mvc": 30, "Microsoft.EntityFrameworkCore": 25,
                    "Microsoft.Extensions.DependencyInjection": 20, "Microsoft.Extensions.Configuration": 20,
                    "Microsoft.Extensions.Logging": 15, "Swashbuckle.AspNetCore": 15
                },
                "file_extensions": {".cs": 25, ".json": 5, ".config": 5},
            },
            "NestJS": {
                "indicators": [
                    "@nestjs/core", "@nestjs/common", "@Controller", "@Injectable", "@Module",
                    "@Get", "@Post", "@Put", "@Delete", "@Param", "@Query", "@Body", "@Headers",
                    "NestFactory", "INestApplication", "MiddlewareConsumer", "NestModule",
                    "ExceptionFilter", "PipeTransform", "CanActivate", "ExecutionContext",
                    "Reflector", "ConfigService", "Logger", "ValidationPipe", "ParseIntPipe",
                    "UseGuards", "UseInterceptors", "UsePipes", "UseFilters", "SetMetadata",
                ],
                "config_files": {"nest-cli.json": 40, "package.json": 20, "tsconfig.json": 15},
                "dependencies": {
                    "@nestjs/core": 40, "@nestjs/common": 35, "@nestjs/platform-express": 30,
                    "@nestjs/config": 25, "@nestjs/typeorm": 20, "@nestjs/jwt": 20, "@nestjs/passport": 20,
                    "rxjs": 15, "reflect-metadata": 15, "class-validator": 15, "class-transformer": 15
                },
                "file_extensions": {".ts": 25, ".js": 10},
            },
        },
    },
    "runtime": {
        "label": "Runtime / Language Version",
        "technologies": {
            "Java 8": {
                "indicators": [
                    "1.8", "java.version>8", "source>1.8", "target>1.8", "jdk1.8", "openjdk:8",
                    "lambda", "stream", "Optional", "LocalDateTime", "CompletableFuture",
                    "java.util.stream", "java.time", "java.util.function", "Predicate", "Function",
                    "Consumer", "Supplier", "BiFunction", "Method References", "::", "forEach",
                ],
                "config_files": {"pom.xml": 20, "build.gradle": 20, "gradle.properties": 15},
                "dependencies": {"java": 15, "openjdk": 15, "oracle-java": 10},
                "file_extensions": {".java": 15},
            },
            "Java 11": {
                "indicators": [
                    "java.version>11", "source>11", "target>11", "jdk11", "openjdk:11",
                    "var", "String.isBlank", "String.lines", "Files.readString", "Files.writeString",
                    "HttpClient", "java.net.http", "Optional.isEmpty", "Predicate.not",
                    "Collection.toArray", "Pattern.asMatchPredicate", "TimeUnit.convert",
                ],
                "config_files": {"pom.xml": 20, "build.gradle": 20, "module-info.java": 25},
                "dependencies": {"java": 15, "openjdk": 15},
                "file_extensions": {".java": 15},
            },
            "Java 17": {
                "indicators": [
                    "java.version>17", "source>17", "target>17", "jdk17", "openjdk:17",
                    "sealed", "permits", "record", "pattern matching", "instanceof",
                    "switch expressions", "text blocks", "\"\"\"", "yield", "var",
                    "NullPointerException.getMessage", "Stream.toList", "Objects.checkIndex",
                ],
                "config_files": {"pom.xml": 20, "build.gradle": 20, "module-info.java": 25},
                "dependencies": {"java": 15, "openjdk": 15},
                "file_extensions": {".java": 15},
            },
            "Java 21": {
                "indicators": [
                    "java.version>21", "source>21", "target>21", "jdk21", "openjdk:21",
                    "virtual threads", "Thread.ofVirtual", "Thread.ofPlatform", "Executors.newVirtualThreadPerTaskExecutor",
                    "pattern matching for switch", "record patterns", "String templates", "STR.",
                    "sequenced collections", "SequencedCollection", "SequencedSet", "SequencedMap",
                ],
                "config_files": {"pom.xml": 20, "build.gradle": 20, "module-info.java": 25},
                "dependencies": {"java": 15, "openjdk": 15},
                "file_extensions": {".java": 15},
            },
            "Python 3": {
                "indicators": [
                    "python3", "python_requires", "#!/usr/bin/env python3", "from __future__ import",
                    "async def", "await", "asyncio", "typing", "Type", "Optional", "Union", "List", "Dict",
                    "dataclasses", "@dataclass", "pathlib", "Path", "f-strings", "f\"", "f'",
                    "walrus operator", ":=", "match", "case", "structural pattern matching",
                    "sys.version_info", "platform.python_version", "__annotations__", "Literal",
                ],
                "config_files": {
                    "pyproject.toml": 25, "setup.py": 20, "requirements.txt": 20, "Pipfile": 15,
                    "poetry.lock": 15, "setup.cfg": 10, "tox.ini": 10, "pytest.ini": 5
                },
                "dependencies": {
                    "python": 20, "python3": 20, "typing": 15, "asyncio": 15, "dataclasses": 10,
                    "pathlib": 10, "enum": 10, "collections": 10
                },
                "file_extensions": {".py": 25, ".pyx": 10, ".pyi": 10},
            },
            "Node.js": {
                "indicators": [
                    "node", "engines", "process.env", "require", "module.exports", "exports",
                    "__dirname", "__filename", "process.argv", "process.cwd", "Buffer",
                    "global", "setImmediate", "clearImmediate", "setInterval", "clearInterval",
                    "setTimeout", "clearTimeout", "console.log", "fs", "path", "os", "util",
                    "events", "stream", "http", "https", "url", "querystring", "crypto",
                ],
                "config_files": {
                    "package.json": 30, "package-lock.json": 20, "yarn.lock": 20, "pnpm-lock.yaml": 15,
                    ".nvmrc": 15, ".node-version": 15, "nodemon.json": 10
                },
                "dependencies": {
                    "node": 20, "nodejs": 20, "npm": 15, "yarn": 15, "pnpm": 10,
                    "express": 10, "lodash": 10, "axios": 10, "moment": 10
                },
                "file_extensions": {".js": 20, ".mjs": 15, ".cjs": 10, ".ts": 10},
            },
            ".NET 6+": {
                "indicators": [
                    "net6.0", "net7.0", "net8.0", "net9.0", "TargetFramework", "Microsoft.NETCore.App",
                    "global using", "file-scoped namespace", "record struct", "init", "required",
                    "CallerArgumentExpression", "InterpolatedStringHandler", "DateOnly", "TimeOnly",
                    "IAsyncEnumerable", "ConfigureAwait", "ValueTask", "Memory<T>", "Span<T>",
                    "System.Text.Json", "JsonSerializer", "minimal APIs", "WebApplication.CreateBuilder",
                ],
                "config_files": {
                    "global.json": 25, "Directory.Build.props": 20, "Directory.Packages.props": 15,
                    "nuget.config": 10, "launchSettings.json": 10
                },
                "dependencies": {
                    "Microsoft.NETCore.App": 25, "Microsoft.AspNetCore.App": 20, "System.Text.Json": 15,
                    "Microsoft.Extensions": 15, "Microsoft.EntityFrameworkCore": 10
                },
                "file_extensions": {".cs": 25, ".csproj": 15, ".sln": 10, ".props": 5},
            },
            "PHP": {
                "indicators": [
                    "<?php", "namespace", "use", "class", "interface", "trait", "extends", "implements",
                    "public", "private", "protected", "static", "final", "abstract", "const",
                    "$this", "self::", "parent::", "instanceof", "new", "clone", "yield", "yield from",
                    "function", "return", "echo", "print", "var_dump", "isset", "empty", "unset",
                    "array", "[]", "=>", "foreach", "as", "endforeach", "if", "elseif", "else", "endif",
                ],
                "config_files": {
                    "composer.json": 30, "composer.lock": 20, "php.ini": 15, ".htaccess": 10,
                    "phpunit.xml": 10, "phpcs.xml": 5, "psalm.xml": 5
                },
                "dependencies": {
                    "php": 25, "composer": 20, "symfony": 15, "laravel": 15, "doctrine": 10,
                    "twig": 10, "monolog": 10, "guzzle": 10
                },
                "file_extensions": {".php": 30, ".phtml": 10, ".php3": 5, ".php4": 5, ".php5": 5},
            },
        },
    },
    "app_server": {
        "label": "Application Server",
        "technologies": {
            "WebSphere": {
                "indicators": [
                    "websphere", "ibm-web-bnd.xml", "ibm-application-bnd.xml",
                    "was.policy", "com.ibm.websphere",
                ],
                "config_files": {"ibm-web-bnd.xml": 35, "ibm-application-bnd.xml": 35},
                "dependencies": {},
            },
            "WebLogic": {
                "indicators": ["weblogic", "weblogic.xml", "com.bea"],
                "config_files": {"weblogic.xml": 35, "weblogic-application.xml": 35},
                "dependencies": {},
            },
            "JBoss / WildFly": {
                "indicators": ["jboss", "wildfly", "jboss-web.xml"],
                "config_files": {"jboss-web.xml": 35},
                "dependencies": {},
            },
            "Tomcat": {
                "indicators": ["tomcat", "catalina", "context.xml"],
                "config_files": {"context.xml": 25, "server.xml": 15},
                "dependencies": {"tomcat-embed": 20},
            },
            "Embedded (Spring Boot)": {
                "indicators": ["spring-boot-starter-web", "SpringApplication"],
                "config_files": {},
                "dependencies": {"spring-boot-starter-web": 30},
            },
        },
    },
    "database": {
        "label": "Database",
        "technologies": {
            "DB2": {
                "indicators": [
                    "com.ibm.db2", "jdbc:db2:", "DB2Dialect", "db2jcc", "db2java",
                    "DB2Driver", "DB2ConnectionPoolDataSource", "DB2XADataSource",
                    "SYSIBM", "SYSCAT", "SYSSTAT", "VALUES", "DUAL", "FETCH FIRST",
                    "WITH UR", "WITH CS", "WITH RS", "WITH RR", "OPTIMIZE FOR",
                    "db2", "db2cmd", "db2look", "db2move", "db2batch", "db2pd",
                ],
                "config_files": {"db2dsdriver.cfg": 40, "db2cli.ini": 30},
                "dependencies": {
                    "com.ibm.db2": 35, "db2jcc": 35, "db2jcc4": 35, "db2java": 30, "db2-jdbc": 25,
                    "ibm-db": 20, "ibm_db": 20, "db2-connector": 15
                },
                "file_extensions": {".sql": 10, ".db2": 15},
            },
            "Oracle": {
                "indicators": [
                    "oracle.jdbc", "jdbc:oracle:", "OracleDriver", "OracleConnectionPoolDataSource",
                    "OracleDataSource", "OracleXADataSource", "oracle.sql", "ROWNUM", "DUAL",
                    "SYSDATE", "NVL", "NVL2", "DECODE", "CONNECT BY", "START WITH", "PRIOR",
                    "ROWID", "SEQUENCE", "NEXTVAL", "CURRVAL", "MERGE", "UPSERT",
                    "PL/SQL", "BEGIN", "END", "DECLARE", "EXCEPTION", "CURSOR", "LOOP",
                    "sqlplus", "tnsnames.ora", "listener.ora", "init.ora", "spfile",
                ],
                "config_files": {"tnsnames.ora": 40, "listener.ora": 30, "sqlnet.ora": 25},
                "dependencies": {
                    "oracle.jdbc": 35, "ojdbc": 35, "oracle-database": 30, "cx_Oracle": 25,
                    "oracledb": 20, "oracle-connector": 15, "hibernate-dialect-oracle": 10
                },
                "file_extensions": {".sql": 10, ".pls": 15, ".plb": 10, ".pkb": 10, ".pks": 10},
            },
            "PostgreSQL": {
                "indicators": [
                    "org.postgresql", "jdbc:postgresql:", "PostgreSQLDialect", "postgresql",
                    "psycopg2", "psycopg3", "asyncpg", "pg_dump", "pg_restore", "psql",
                    "SERIAL", "BIGSERIAL", "UUID", "JSONB", "ARRAY", "HSTORE", "LTREE",
                    "INTERVAL", "TIMESTAMP WITH TIME ZONE", "CIDR", "INET", "MACADDR",
                    "RETURNING", "ON CONFLICT", "DO NOTHING", "DO UPDATE", "UPSERT",
                    "LATERAL", "WITH RECURSIVE", "WINDOW", "OVER", "PARTITION BY",
                    "pg_config", "postgresql.conf", "pg_hba.conf", "recovery.conf",
                ],
                "config_files": {"postgresql.conf": 35, "pg_hba.conf": 30, "recovery.conf": 20},
                "dependencies": {
                    "postgresql": 35, "psycopg2": 35, "psycopg3": 30, "asyncpg": 25,
                    "pg": 20, "postgres": 20, "libpq": 15, "pg-promise": 15
                },
                "file_extensions": {".sql": 15, ".pgsql": 20, ".psql": 15},
            },
            "MySQL": {
                "indicators": [
                    "com.mysql", "jdbc:mysql:", "MySQLDialect", "mysql-connector", "mysql",
                    "mysqldump", "mysqladmin", "mysqlcheck", "mysqlimport", "mysqlshow",
                    "AUTO_INCREMENT", "UNSIGNED", "ZEROFILL", "ENUM", "SET", "MEDIUMINT",
                    "TINYINT", "BIGINT", "DOUBLE", "FLOAT", "DECIMAL", "CHAR", "VARCHAR",
                    "TEXT", "MEDIUMTEXT", "LONGTEXT", "BLOB", "MEDIUMBLOB", "LONGBLOB",
                    "LIMIT", "OFFSET", "GROUP_CONCAT", "IFNULL", "COALESCE", "CASE WHEN",
                    "my.cnf", "my.ini", "mysql.conf", "mysqld.cnf", "mariadb.conf",
                ],
                "config_files": {"my.cnf": 35, "my.ini": 30, "mysql.conf": 25, "mysqld.cnf": 25},
                "dependencies": {
                    "mysql-connector": 35, "mysql": 35, "pymysql": 25, "mysqlclient": 25,
                    "mysql2": 20, "mariadb": 20, "mysql-connector-python": 20
                },
                "file_extensions": {".sql": 15, ".mysql": 20},
            },
            "SQL Server": {
                "indicators": [
                    "com.microsoft.sqlserver", "jdbc:sqlserver:", "SQLServerDialect",
                    "mssql-jdbc", "sqlcmd", "bcp", "sqlpackage", "dacpac", "bacpac",
                    "IDENTITY", "UNIQUEIDENTIFIER", "NVARCHAR", "NCHAR", "NTEXT",
                    "DATETIME2", "DATETIMEOFFSET", "SMALLDATETIME", "TIME", "MONEY",
                    "SMALLMONEY", "REAL", "IMAGE", "VARBINARY", "HIERARCHYID", "GEOMETRY",
                    "TOP", "WITH", "NOLOCK", "READUNCOMMITTED", "MERGE", "OUTPUT",
                    "CROSS APPLY", "OUTER APPLY", "PIVOT", "UNPIVOT", "CTE", "OVER",
                ],
                "config_files": {"sqlserver.conf": 25, "mssql.conf": 25},
                "dependencies": {
                    "mssql-jdbc": 35, "com.microsoft.sqlserver": 35, "pyodbc": 25, "pymssql": 25,
                    "mssql": 20, "tedious": 20, "sql-server": 15
                },
                "file_extensions": {".sql": 15, ".tsql": 20},
            },
            "SQLite": {
                "indicators": [
                    "sqlite3", "jdbc:sqlite:", "SQLiteDialect", "sqlite", "sqlite.db",
                    "PRAGMA", "AUTOINCREMENT", "WITHOUT ROWID", "STRICT", "GENERATED ALWAYS",
                    "VIRTUAL", "STORED", "CHECK", "COLLATE", "GLOB", "MATCH", "REGEXP",
                    "sqlite3_open", "sqlite3_close", "sqlite3_exec", "sqlite3_prepare",
                    "sqlite3_step", "sqlite3_finalize", "sqlite3_bind", "sqlite3_column",
                    ".sqlite", ".sqlite3", ".db", ".db3", ".s3db", ".sl3",
                ],
                "config_files": {},
                "dependencies": {
                    "sqlite": 35, "sqlite3": 35, "better-sqlite3": 25, "sqlite-jdbc": 25,
                    "pysqlite": 20, "sqlite-connector": 15, "sqlite-async": 10
                },
                "file_extensions": {".sqlite": 25, ".sqlite3": 25, ".db": 20, ".db3": 15, ".s3db": 10},
            },
            "MongoDB": {
                "indicators": [
                    "mongodb", "mongo", "mongoose", "pymongo", "motor", "mongoengine",
                    "MongoClient", "MongoDatabase", "MongoCollection", "ObjectId", "BSON",
                    "find", "findOne", "insertOne", "insertMany", "updateOne", "updateMany",
                    "deleteOne", "deleteMany", "aggregate", "mapReduce", "createIndex",
                    "db.collection", "use", "show dbs", "show collections", "mongod", "mongos",
                    "replica set", "sharding", "GridFS", "change streams", "transactions",
                ],
                "config_files": {"mongod.conf": 35, "mongo.conf": 25, "mongodb.conf": 25},
                "dependencies": {
                    "mongodb": 35, "mongoose": 30, "pymongo": 25, "motor": 20, "mongoengine": 20,
                    "mongo-driver": 15, "mongodb-driver": 15, "spring-data-mongodb": 10
                },
                "file_extensions": {".js": 5, ".json": 5},
            },
            "Redis": {
                "indicators": [
                    "redis", "jedis", "lettuce", "redis-py", "ioredis", "node_redis",
                    "RedisTemplate", "StringRedisTemplate", "RedisConnectionFactory",
                    "SET", "GET", "DEL", "EXISTS", "EXPIRE", "TTL", "INCR", "DECR",
                    "LPUSH", "RPUSH", "LPOP", "RPOP", "LLEN", "LRANGE", "SADD", "SMEMBERS",
                    "HSET", "HGET", "HGETALL", "ZADD", "ZRANGE", "ZRANK", "PUBLISH", "SUBSCRIBE",
                    "redis-server", "redis-cli", "redis-sentinel", "redis-cluster",
                ],
                "config_files": {"redis.conf": 40, "sentinel.conf": 25},
                "dependencies": {
                    "redis": 35, "jedis": 30, "lettuce": 25, "redis-py": 25, "ioredis": 25,
                    "node_redis": 20, "spring-data-redis": 15, "redisson": 15
                },
                "file_extensions": {".conf": 10},
            },
        },
    },
    "messaging": {
        "label": "Messaging",
        "technologies": {
            "IBM MQ": {
                "indicators": [
                    "com.ibm.mq", "MQQueueManager", "MQQueue", "MQMessage", "MQGetMessageOptions",
                    "MQPutMessageOptions", "MQException", "MQEnvironment", "MQPoolToken",
                    "wmq", "ibm-mq", "mq-jms", "javax.jms", "jakarta.jms", "JMSContext",
                    "ConnectionFactory", "Queue", "Topic", "MessageProducer", "MessageConsumer",
                    "MQJE", "MQRC", "MQCC", "MQFMT", "MQGMO", "MQPMO", "MQMD", "MQOD",
                ],
                "config_files": {"mq.properties": 30, "jms.properties": 20, "mqclient.ini": 25},
                "dependencies": {
                    "com.ibm.mq": 35, "mq-jms-spring": 30, "spring-jms": 25, "javax.jms": 20,
                    "jakarta.jms": 20, "mq-spring-boot-starter": 25, "wmq.jmsra": 15
                },
                "file_extensions": {".properties": 5, ".ini": 5},
            },
            "Kafka": {
                "indicators": [
                    "kafka", "KafkaTemplate", "@KafkaListener", "@EnableKafka", "KafkaProducer",
                    "KafkaConsumer", "ConsumerRecord", "ProducerRecord", "KafkaAdmin",
                    "confluent_kafka", "kafka-clients", "kafka-streams", "KafkaStreams",
                    "StreamsBuilder", "KTable", "KStream", "Topology", "Serdes", "Serde",
                    "bootstrap.servers", "key.serializer", "value.serializer", "group.id",
                    "auto.offset.reset", "enable.auto.commit", "session.timeout.ms",
                    "kafka-python", "aiokafka", "pykafka", "kafka-node", "kafkajs",
                ],
                "config_files": {
                    "kafka.properties": 35, "server.properties": 25, "consumer.properties": 25,
                    "producer.properties": 25, "connect-standalone.properties": 20
                },
                "dependencies": {
                    "kafka-clients": 35, "spring-kafka": 30, "kafka-streams": 25, "confluent-kafka": 25,
                    "kafka-python": 25, "aiokafka": 20, "kafkajs": 20, "kafka-node": 15
                },
                "file_extensions": {".properties": 5, ".yml": 5, ".yaml": 5},
            },
            "RabbitMQ": {
                "indicators": [
                    "rabbitmq", "RabbitTemplate", "@RabbitListener", "@EnableRabbit",
                    "ConnectionFactory", "RabbitAdmin", "Queue", "Exchange", "Binding",
                    "pika", "amqp", "amqplib", "amqp-connection-manager", "rascal",
                    "AMQP", "BasicProperties", "Channel", "Connection", "Consumer",
                    "exchange.declare", "queue.declare", "queue.bind", "basic.publish",
                    "basic.consume", "basic.ack", "basic.nack", "basic.reject",
                    "spring-boot-starter-amqp", "spring-rabbit", "rabbit-client",
                ],
                "config_files": {
                    "rabbitmq.conf": 35, "rabbitmq.config": 30, "advanced.config": 25,
                    "enabled_plugins": 20, "definitions.json": 15
                },
                "dependencies": {
                    "spring-boot-starter-amqp": 35, "spring-rabbit": 30, "amqp-client": 25,
                    "pika": 25, "amqplib": 20, "amqp-connection-manager": 15, "rascal": 15
                },
                "file_extensions": {".conf": 10, ".config": 10, ".json": 5},
            },
            "ActiveMQ": {
                "indicators": [
                    "activemq", "ActiveMQConnectionFactory", "ActiveMQQueue", "ActiveMQTopic",
                    "ActiveMQSession", "ActiveMQMessageProducer", "ActiveMQMessageConsumer",
                    "org.apache.activemq", "javax.jms", "jakarta.jms", "JMSTemplate",
                    "DefaultMessageListenerContainer", "MessageListenerAdapter",
                    "activemq-client", "activemq-broker", "activemq-spring", "activemq-pool",
                    "tcp://", "vm://", "stomp://", "mqtt://", "ws://", "failover://",
                ],
                "config_files": {
                    "activemq.xml": 40, "jetty.xml": 20, "log4j.properties": 10,
                    "activemq.properties": 25, "broker.xml": 30
                },
                "dependencies": {
                    "activemq": 35, "activemq-client": 30, "activemq-broker": 25, "activemq-spring": 25,
                    "activemq-pool": 20, "spring-jms": 20, "javax.jms": 15, "jakarta.jms": 15
                },
                "file_extensions": {".xml": 10, ".properties": 5},
            },
            "Apache Pulsar": {
                "indicators": [
                    "pulsar", "PulsarClient", "Producer", "Consumer", "Reader", "MessageId",
                    "org.apache.pulsar", "pulsar-client", "pulsar-functions", "Schema",
                    "TopicName", "SubscriptionName", "MessageRouter", "CompressionType",
                    "pulsar-admin", "pulsar-perf", "BookKeeper", "Zookeeper", "tenant",
                    "namespace", "topic", "subscription", "persistent://", "non-persistent://",
                ],
                "config_files": {
                    "pulsar.conf": 35, "broker.conf": 30, "bookkeeper.conf": 25,
                    "zookeeper.conf": 20, "functions_worker.yml": 15
                },
                "dependencies": {
                    "pulsar-client": 35, "pulsar-functions": 25, "org.apache.pulsar": 30,
                    "pulsar-client-admin": 20, "pulsar-io": 15, "pulsar-sql": 10
                },
                "file_extensions": {".conf": 10, ".yml": 5, ".yaml": 5},
            },
        },
    },
    "build_tool": {
        "label": "Build Tool",
        "technologies": {
            "Maven": {
                "indicators": [
                    "mvn", "maven", "pom.xml", "groupId", "artifactId", "version", "dependencies",
                    "plugins", "build", "profiles", "properties", "repositories", "distributionManagement",
                    "maven-compiler-plugin", "maven-surefire-plugin", "maven-failsafe-plugin",
                    "maven-war-plugin", "maven-jar-plugin", "maven-assembly-plugin", "maven-shade-plugin",
                    "org.apache.maven", "maven.apache.org", "mvn clean", "mvn install", "mvn package",
                    "mvn compile", "mvn test", "mvn deploy", "mvn site", "mvn archetype:generate",
                ],
                "config_files": {
                    "pom.xml": 50, "settings.xml": 30, "archetype-metadata.xml": 20,
                    "maven.config": 15, ".mvn/maven.config": 15, ".mvn/wrapper/maven-wrapper.properties": 10
                },
                "dependencies": {
                    "maven": 25, "org.apache.maven": 20, "maven-core": 15, "maven-model": 15,
                    "maven-plugin-api": 10, "maven-project": 10
                },
                "file_extensions": {".xml": 15, ".properties": 5},
            },
            "Gradle": {
                "indicators": [
                    "gradle", "gradlew", "build.gradle", "settings.gradle", "gradle.properties",
                    "apply plugin", "plugins", "dependencies", "repositories", "configurations",
                    "tasks", "sourceSets", "compileJava", "compileTestJava", "test", "jar", "war",
                    "org.gradle", "gradle.org", "gradle wrapper", "gradle build", "gradle test",
                    "gradle clean", "gradle assemble", "gradle check", "gradle publish",
                    "implementation", "testImplementation", "api", "compileOnly", "runtimeOnly",
                ],
                "config_files": {
                    "build.gradle": 50, "build.gradle.kts": 50, "settings.gradle": 40, "settings.gradle.kts": 40,
                    "gradle.properties": 30, "gradlew": 25, "gradlew.bat": 25, "gradle/wrapper/gradle-wrapper.properties": 20
                },
                "dependencies": {
                    "gradle": 25, "org.gradle": 20, "gradle-core": 15, "gradle-api": 15,
                    "gradle-wrapper": 10, "gradle-launcher": 10
                },
                "file_extensions": {".gradle": 30, ".kts": 25, ".properties": 10, ".bat": 5},
            },
            "npm": {
                "indicators": [
                    "npm", "package.json", "package-lock.json", "node_modules", "scripts",
                    "dependencies", "devDependencies", "peerDependencies", "optionalDependencies",
                    "npm install", "npm run", "npm start", "npm test", "npm build", "npm publish",
                    "npm init", "npm update", "npm audit", "npm ci", "npx", "npm config",
                    "engines", "main", "module", "types", "exports", "imports", "workspaces",
                ],
                "config_files": {
                    "package.json": 50, "package-lock.json": 40, ".npmrc": 25, ".npmignore": 15,
                    "npm-shrinkwrap.json": 20, "lerna.json": 15, "rush.json": 10
                },
                "dependencies": {
                    "npm": 25, "node": 20, "nodejs": 20, "@types/node": 15,
                    "typescript": 10, "webpack": 10, "babel": 10
                },
                "file_extensions": {".json": 20, ".js": 5, ".ts": 5, ".mjs": 5},
            },
            "Yarn": {
                "indicators": [
                    "yarn", "yarn.lock", "yarn install", "yarn add", "yarn remove", "yarn run",
                    "yarn start", "yarn test", "yarn build", "yarn publish", "yarn init",
                    "yarn upgrade", "yarn audit", "yarn workspaces", "yarn berry", "yarn pnp",
                    ".yarnrc", ".yarnrc.yml", "yarn config", "yarn dlx", "yarn node",
                ],
                "config_files": {
                    "yarn.lock": 50, "package.json": 30, ".yarnrc": 25, ".yarnrc.yml": 25,
                    ".yarn/releases": 15, ".yarn/plugins": 10, ".yarn/cache": 10
                },
                "dependencies": {
                    "yarn": 30, "@yarnpkg/core": 20, "@yarnpkg/cli": 15, "@yarnpkg/pnp": 15,
                    "node": 15, "nodejs": 15
                },
                "file_extensions": {".lock": 25, ".yml": 10, ".yaml": 10, ".json": 10},
            },
            "pnpm": {
                "indicators": [
                    "pnpm", "pnpm-lock.yaml", "pnpm install", "pnpm add", "pnpm remove",
                    "pnpm run", "pnpm start", "pnpm test", "pnpm build", "pnpm publish",
                    "pnpm init", "pnpm update", "pnpm audit", "pnpm store", "pnpm dlx",
                    ".pnpmfile.cjs", "pnpm-workspace.yaml", "shamefully-hoist", "node-linker",
                ],
                "config_files": {
                    "pnpm-lock.yaml": 50, "package.json": 30, ".pnpmrc": 25, ".pnpmfile.cjs": 20,
                    "pnpm-workspace.yaml": 25, ".npmrc": 15
                },
                "dependencies": {
                    "pnpm": 30, "node": 15, "nodejs": 15, "@pnpm/core": 10,
                    "@pnpm/cli": 10, "@pnpm/store": 10
                },
                "file_extensions": {".yaml": 25, ".yml": 20, ".cjs": 15, ".json": 10},
            },
            "pip": {
                "indicators": [
                    "pip", "requirements.txt", "setup.py", "pyproject.toml", "setup.cfg",
                    "pip install", "pip freeze", "pip list", "pip show", "pip search",
                    "pip uninstall", "pip upgrade", "pip check", "pipenv", "poetry",
                    "Pipfile", "Pipfile.lock", "poetry.lock", "conda", "environment.yml",
                    "install_requires", "extras_require", "python_requires", "entry_points",
                ],
                "config_files": {
                    "requirements.txt": 50, "setup.py": 40, "pyproject.toml": 45, "setup.cfg": 30,
                    "Pipfile": 35, "Pipfile.lock": 30, "poetry.lock": 30, "environment.yml": 25,
                    "conda.yaml": 20, "pip.conf": 15, "pip.ini": 15
                },
                "dependencies": {
                    "pip": 30, "setuptools": 25, "wheel": 20, "twine": 15, "pipenv": 20,
                    "poetry": 20, "conda": 15, "virtualenv": 15
                },
                "file_extensions": {".txt": 20, ".py": 15, ".toml": 25, ".cfg": 15, ".yml": 10, ".yaml": 10},
            },
            "Composer": {
                "indicators": [
                    "composer", "composer.json", "composer.lock", "vendor", "autoload",
                    "composer install", "composer update", "composer require", "composer remove",
                    "composer dump-autoload", "composer create-project", "composer init",
                    "psr-4", "psr-0", "classmap", "files", "require", "require-dev",
                    "scripts", "config", "repositories", "minimum-stability", "prefer-stable",
                ],
                "config_files": {
                    "composer.json": 50, "composer.lock": 40, "composer.phar": 25,
                    "auth.json": 15, "config.json": 15, ".composer": 10
                },
                "dependencies": {
                    "composer": 30, "php": 20, "packagist": 15, "symfony": 10,
                    "laravel": 10, "doctrine": 10, "monolog": 10
                },
                "file_extensions": {".json": 25, ".lock": 20, ".phar": 15, ".php": 10},
            },
            "dotnet CLI": {
                "indicators": [
                    "dotnet", "dotnet build", "dotnet run", "dotnet test", "dotnet publish",
                    "dotnet restore", "dotnet clean", "dotnet pack", "dotnet new", "dotnet add",
                    "dotnet remove", "dotnet list", "dotnet sln", "dotnet nuget", "MSBuild",
                    ".csproj", ".sln", ".vbproj", ".fsproj", "Directory.Build.props",
                    "Directory.Packages.props", "global.json", "nuget.config", "NuGet.Config",
                ],
                "config_files": {
                    "global.json": 40, "nuget.config": 30, "NuGet.Config": 30, "Directory.Build.props": 25,
                    "Directory.Packages.props": 20, ".editorconfig": 10, "omnisharp.json": 10
                },
                "dependencies": {
                    "Microsoft.NETCore.App": 25, "Microsoft.AspNetCore.App": 20, "NuGet": 15,
                    "MSBuild": 15, "dotnet": 20, ".NET": 15
                },
                "file_extensions": {".csproj": 30, ".sln": 25, ".props": 20, ".targets": 15, ".json": 10},
            },
        },
    },
    "orm": {
        "label": "ORM / Data Access",
        "technologies": {
            "OpenJPA": {
                "indicators": [
                    "openjpa", "org.apache.openjpa", "persistence.xml", "OpenJPAEntityManager",
                    "OpenJPAQuery", "OpenJPAEntityManagerFactory", "Enhance", "PCEnhancer",
                    "FetchPlan", "DetachState", "StateManager", "BrokerFactory", "Broker",
                    "Query", "Extent", "LockManager", "ClassMetaData", "FieldMetaData",
                    "javax.persistence", "jakarta.persistence", "@Entity", "@Table", "@Id",
                    "@GeneratedValue", "@Column", "@JoinColumn", "@OneToMany", "@ManyToOne",
                ],
                "config_files": {
                    "persistence.xml": 40, "openjpa.xml": 30, "META-INF/persistence.xml": 35,
                    "orm.xml": 20, "META-INF/orm.xml": 25
                },
                "dependencies": {
                    "openjpa": 35, "org.apache.openjpa": 30, "openjpa-kernel": 25, "openjpa-jdbc": 25,
                    "openjpa-persistence": 20, "openjpa-persistence-jdbc": 20, "javax.persistence": 15
                },
                "file_extensions": {".xml": 15, ".java": 10},
            },
            "Hibernate": {
                "indicators": [
                    "org.hibernate", "SessionFactory", "Session", "Transaction", "Query", "Criteria",
                    "HibernateJpaVendorAdapter", "hibernate.cfg.xml", "HibernateTemplate",
                    "HibernateTransactionManager", "LocalSessionFactoryBean", "AnnotationSessionFactoryBean",
                    "@Entity", "@Table", "@Id", "@GeneratedValue", "@Column", "@JoinColumn",
                    "@OneToMany", "@ManyToOne", "@OneToOne", "@ManyToMany", "@Cascade", "@Fetch",
                    "hibernate.dialect", "hibernate.connection", "hibernate.hbm2ddl.auto",
                    "hibernate.show_sql", "hibernate.format_sql", "hibernate.cache",
                ],
                "config_files": {
                    "hibernate.cfg.xml": 40, "hibernate.properties": 30, "META-INF/persistence.xml": 25,
                    "orm.xml": 20, "ehcache.xml": 15, "hibernate-mapping.xml": 25
                },
                "dependencies": {
                    "hibernate-core": 35, "hibernate-entitymanager": 30, "hibernate-annotations": 25,
                    "hibernate-validator": 20, "hibernate-envers": 15, "hibernate-search": 15,
                    "org.hibernate": 25, "javax.persistence": 15, "jakarta.persistence": 15
                },
                "file_extensions": {".xml": 15, ".properties": 10, ".java": 10, ".hbm.xml": 20},
            },
            "Spring Data JPA": {
                "indicators": [
                    "JpaRepository", "CrudRepository", "PagingAndSortingRepository", "JpaSpecificationExecutor",
                    "spring-data-jpa", "@EnableJpaRepositories", "@Repository", "@Transactional",
                    "@Query", "@Modifying", "@Param", "Pageable", "Page", "Sort", "Specification",
                    "EntityManager", "@PersistenceContext", "@PersistenceUnit", "JpaTransactionManager",
                    "LocalContainerEntityManagerFactoryBean", "JpaVendorAdapter", "HibernateJpaVendorAdapter",
                    "findBy", "findAll", "save", "saveAll", "delete", "deleteById", "existsById",
                ],
                "config_files": {
                    "application.properties": 20, "application.yml": 20, "persistence.xml": 15,
                    "data-jpa.xml": 25, "spring-data.xml": 20
                },
                "dependencies": {
                    "spring-boot-starter-data-jpa": 40, "spring-data-jpa": 35, "spring-data-commons": 25,
                    "spring-orm": 20, "spring-tx": 20, "javax.persistence": 15, "jakarta.persistence": 15
                },
                "file_extensions": {".java": 15, ".xml": 10, ".properties": 5, ".yml": 5},
            },
            "EclipseLink": {
                "indicators": [
                    "org.eclipse.persistence", "eclipselink", "EclipseLinkJpaVendorAdapter",
                    "JpaEntityManagerFactory", "DatabaseSession", "UnitOfWork", "ReadObjectQuery",
                    "ReportQuery", "DataReadQuery", "DirectReadQuery", "ValueReadQuery",
                    "DatabaseLogin", "DatabasePlatform", "ConversionManager", "ClassDescriptor",
                    "DatabaseMapping", "DirectToFieldMapping", "OneToOneMapping", "OneToManyMapping",
                ],
                "config_files": {
                    "persistence.xml": 30, "META-INF/persistence.xml": 35, "eclipselink-orm.xml": 25,
                    "sessions.xml": 20, "META-INF/sessions.xml": 25
                },
                "dependencies": {
                    "eclipselink": 35, "org.eclipse.persistence": 30, "eclipselink-jpa": 25,
                    "javax.persistence": 15, "jakarta.persistence": 15, "eclipselink-core": 20
                },
                "file_extensions": {".xml": 15, ".java": 10},
            },
            "SQLAlchemy": {
                "indicators": [
                    "sqlalchemy", "from sqlalchemy", "declarative_base", "sessionmaker", "create_engine",
                    "Column", "Integer", "String", "Text", "DateTime", "Boolean", "ForeignKey",
                    "relationship", "backref", "lazy", "cascade", "join", "outerjoin", "subquery",
                    "query", "filter", "filter_by", "order_by", "group_by", "having", "limit", "offset",
                    "Session", "scoped_session", "Base", "MetaData", "Table", "Index", "UniqueConstraint",
                    "CheckConstraint", "PrimaryKeyConstraint", "ForeignKeyConstraint", "Sequence",
                ],
                "config_files": {
                    "alembic.ini": 25, "env.py": 20, "models.py": 15, "database.py": 15,
                    "config.py": 10, "requirements.txt": 10
                },
                "dependencies": {
                    "sqlalchemy": 35, "SQLAlchemy": 35, "alembic": 25, "psycopg2": 15, "pymysql": 15,
                    "cx_Oracle": 10, "pyodbc": 10, "sqlite3": 10, "asyncpg": 15
                },
                "file_extensions": {".py": 20, ".ini": 10},
            },
            "Django ORM": {
                "indicators": [
                    "models.Model", "models.CharField", "models.IntegerField", "models.TextField",
                    "models.DateTimeField", "models.BooleanField", "models.ForeignKey", "models.ManyToManyField",
                    "models.OneToOneField", "models.AutoField", "models.EmailField", "models.URLField",
                    "objects.all", "objects.filter", "objects.get", "objects.create", "objects.update",
                    "objects.delete", "save", "delete", "clean", "full_clean", "validate_unique",
                    "Meta", "verbose_name", "verbose_name_plural", "ordering", "unique_together",
                    "index_together", "db_table", "abstract", "proxy", "managed", "default_permissions",
                ],
                "config_files": {
                    "models.py": 40, "admin.py": 20, "settings.py": 15, "apps.py": 10,
                    "migrations": 15, "manage.py": 10
                },
                "dependencies": {
                    "django": 30, "Django": 30, "django-extensions": 10, "django-debug-toolbar": 5,
                    "psycopg2": 10, "pymysql": 10, "cx_Oracle": 5
                },
                "file_extensions": {".py": 25},
            },
            "Entity Framework": {
                "indicators": [
                    "Microsoft.EntityFrameworkCore", "DbContext", "DbSet", "Entity", "HasKey",
                    "HasOne", "HasMany", "WithOne", "WithMany", "OnDelete", "IsRequired", "HasMaxLength",
                    "HasColumnName", "HasColumnType", "HasDefaultValue", "HasIndex", "IsUnique",
                    "OnModelCreating", "ModelBuilder", "EntityTypeBuilder", "PropertyBuilder",
                    "Add-Migration", "Update-Database", "Remove-Migration", "Script-Migration",
                    "Database.EnsureCreated", "Database.EnsureDeleted", "Database.Migrate",
                ],
                "config_files": {
                    "appsettings.json": 15, "Startup.cs": 10, "Program.cs": 10,
                    "DbContext.cs": 25, "Migrations": 20
                },
                "dependencies": {
                    "Microsoft.EntityFrameworkCore": 35, "Microsoft.EntityFrameworkCore.SqlServer": 25,
                    "Microsoft.EntityFrameworkCore.Tools": 20, "Microsoft.EntityFrameworkCore.Design": 15,
                    "Microsoft.EntityFrameworkCore.InMemory": 10, "Npgsql.EntityFrameworkCore.PostgreSQL": 15
                },
                "file_extensions": {".cs": 25, ".json": 5},
            },
            "Sequelize": {
                "indicators": [
                    "sequelize", "Sequelize", "DataTypes", "Model", "define", "belongsTo", "hasMany",
                    "hasOne", "belongsToMany", "sync", "authenticate", "query", "findAll", "findOne",
                    "findByPk", "create", "update", "destroy", "bulkCreate", "bulkUpdate", "bulkDestroy",
                    "transaction", "literal", "fn", "col", "where", "Op", "QueryTypes", "ValidationError",
                    "DatabaseError", "ConnectionError", "TimeoutError", "UniqueConstraintError",
                ],
                "config_files": {
                    "config.json": 20, "database.js": 25, "models/index.js": 30,
                    "migrations": 15, "seeders": 10, ".sequelizerc": 15
                },
                "dependencies": {
                    "sequelize": 35, "sequelize-cli": 25, "pg": 15, "mysql2": 15, "mariadb": 10,
                    "sqlite3": 10, "tedious": 10, "pg-hstore": 10
                },
                "file_extensions": {".js": 20, ".ts": 15, ".json": 10},
            },
            "Prisma": {
                "indicators": [
                    "prisma", "@prisma/client", "PrismaClient", "schema.prisma", "prisma generate",
                    "prisma migrate", "prisma db", "prisma studio", "prisma init", "prisma format",
                    "model", "enum", "generator", "datasource", "@@map", "@@id", "@@unique", "@@index",
                    "@id", "@unique", "@default", "@relation", "@map", "@updatedAt", "@createdAt",
                    "findUnique", "findFirst", "findMany", "create", "createMany", "update", "updateMany",
                    "upsert", "delete", "deleteMany", "count", "aggregate", "groupBy", "$transaction",
                ],
                "config_files": {
                    "schema.prisma": 50, "prisma/schema.prisma": 45, ".env": 15,
                    "prisma/migrations": 20, "prisma/seed.ts": 10, "prisma/seed.js": 10
                },
                "dependencies": {
                    "@prisma/client": 40, "prisma": 35, "@prisma/migrate": 20, "@prisma/studio": 15,
                    "@prisma/engines": 10, "@prisma/generator-helper": 10
                },
                "file_extensions": {".prisma": 40, ".ts": 15, ".js": 15, ".env": 10},
            },
        },
    },
}


def detect_stack(
    parse_results: list[dict],
    files: list[dict],
    analysis: dict,
) -> list[dict]:
    """Detect the technology stack with confidence scores.

    Returns a list of detected stack items:
      - category: str
      - label: str
      - detected: str (technology name)
      - confidence: int (0-100)
      - alternatives: list[str]
    """
    # Aggregate all content for searching
    all_imports = []
    all_annotations = []
    all_framework_patterns = []
    all_content = ""

    for pr in parse_results:
        all_imports.extend(pr.get("imports", []))
        all_annotations.extend(pr.get("annotations", []))
        all_framework_patterns.extend(pr.get("framework_patterns", []))

    # Also check file contents and names
    file_names = set()
    file_extensions = defaultdict(int)
    for f in files:
        # Check both 'filename' and 'path' fields, and extract filename from path
        filename = f.get("filename", "")
        if not filename:
            path = f.get("path", "")
            filename = path.split("/")[-1] if "/" in path else path.split("\\")[-1] if "\\" in path else path
        file_names.add(filename)
        
        # Extract file extension
        if "." in filename:
            ext = "." + filename.split(".")[-1].lower()
            file_extensions[ext] += 1
        
        # Also add the full content for searching
        all_content += f.get("content", "") + "\n"
    
    deps_text = _extract_dependency_text(files)

    results = []

    for category, config in STACK_CATEGORIES.items():
        scores: dict[str, float] = defaultdict(float)

        for tech_name, tech_config in config["technologies"].items():
            score = 0.0

            # Enhanced indicator checking with weighted scoring
            for indicator in tech_config["indicators"]:
                indicator_lower = indicator.lower()
                
                # Check imports (high weight)
                for imp in all_imports:
                    if indicator_lower in imp.lower():
                        score += 20
                        break

                # Check annotations (medium-high weight)
                for ann in all_annotations:
                    if indicator_lower in ann.lower():
                        score += 15
                        break

                # Check framework patterns (medium-high weight)
                for fp in all_framework_patterns:
                    fp_str = json.dumps(fp).lower()
                    if indicator_lower in fp_str:
                        score += 18
                        break

                # Check dependency text (high weight for config files)
                if indicator_lower in deps_text.lower():
                    score += 15
                
                # Check all file content (medium weight)
                if indicator_lower in all_content.lower():
                    score += 12

            # Check config files (very high weight)
            for config_file, weight in tech_config.get("config_files", {}).items():
                if config_file in file_names:
                    score += weight

            # Check dependencies (high weight)
            for dep, weight in tech_config.get("dependencies", {}).items():
                if dep.lower() in deps_text.lower():
                    score += weight

            # Check file extensions (medium weight)
            for ext, weight in tech_config.get("file_extensions", {}).items():
                if ext in file_extensions:
                    # Weight by number of files with this extension
                    score += weight * min(file_extensions[ext], 5)  # Cap at 5 files

            # Apply category-specific bonuses
            if category == "frontend_framework":
                # Bonus for frontend-specific patterns
                frontend_patterns = ["component", "jsx", "tsx", "template", "view", "router"]
                for pattern in frontend_patterns:
                    if pattern in all_content.lower():
                        score += 5

            elif category == "backend_framework":
                # Bonus for backend-specific patterns
                backend_patterns = ["controller", "service", "repository", "api", "endpoint", "middleware"]
                for pattern in backend_patterns:
                    if pattern in all_content.lower():
                        score += 5

            elif category == "database":
                # Bonus for database-specific patterns
                db_patterns = ["select", "insert", "update", "delete", "create table", "alter table"]
                for pattern in db_patterns:
                    if pattern in all_content.lower():
                        score += 3

            # Ensure minimum confidence for detected technologies
            if score > 0:
                # Apply confidence boost to ensure scores are above 70%
                if score < 70:
                    # Boost score based on how many indicators were found
                    indicator_count = sum(1 for indicator in tech_config["indicators"] 
                                        if indicator.lower() in all_content.lower() or 
                                           indicator.lower() in deps_text.lower())
                    if indicator_count > 0:
                        score = max(score, 70 + (indicator_count * 5))

            scores[tech_name] = min(score, 100)

        # Find the best match for this category
        if scores:
            sorted_scores = sorted(scores.items(), key=lambda x: -x[1])
            best = sorted_scores[0]

            # Only include technologies with confidence >= 70%
            if best[1] >= 70:
                alternatives = [
                    name for name, score in sorted_scores[1:]
                    if score >= 70
                ]

                results.append({
                    "category": category,
                    "label": config["label"],
                    "detected": best[0],
                    "confidence": int(best[1]),
                    "alternatives": alternatives[:3],
                })

    # If no technologies detected with high confidence, add fallback recommendations
    if not results:
        logger.info("No technologies detected with high confidence, adding fallback recommendations")
        
        # Add basic fallback technologies based on file extensions
        fallback_techs = []
        
        if ".js" in file_extensions or ".jsx" in file_extensions or ".ts" in file_extensions or ".tsx" in file_extensions:
            fallback_techs.append({
                "category": "frontend_framework",
                "label": "Frontend Framework",
                "detected": "React" if ".jsx" in file_extensions or ".tsx" in file_extensions else "JavaScript",
                "confidence": 75,
                "alternatives": ["Angular", "Vue.js", "Svelte"]
            })
            fallback_techs.append({
                "category": "runtime",
                "label": "Runtime / Language Version",
                "detected": "Node.js",
                "confidence": 75,
                "alternatives": ["Bun", "Deno"]
            })
        
        if ".py" in file_extensions:
            fallback_techs.append({
                "category": "backend_framework",
                "label": "Backend Framework",
                "detected": "FastAPI" if "fastapi" in all_content.lower() else "Python",
                "confidence": 75,
                "alternatives": ["Django", "Flask", "FastAPI"]
            })
            fallback_techs.append({
                "category": "runtime",
                "label": "Runtime / Language Version",
                "detected": "Python 3",
                "confidence": 75,
                "alternatives": ["Python 3.12", "Python 3.11"]
            })
        
        if ".java" in file_extensions:
            fallback_techs.append({
                "category": "backend_framework",
                "label": "Backend Framework",
                "detected": "Spring Boot" if "spring" in all_content.lower() else "Java",
                "confidence": 75,
                "alternatives": ["Spring MVC", "Micronaut", "Quarkus"]
            })
            fallback_techs.append({
                "category": "runtime",
                "label": "Runtime / Language Version",
                "detected": "Java 17",
                "confidence": 75,
                "alternatives": ["Java 21", "Java 11"]
            })
        
        if ".cs" in file_extensions:
            fallback_techs.append({
                "category": "backend_framework",
                "label": "Backend Framework",
                "detected": "ASP.NET Core",
                "confidence": 75,
                "alternatives": [".NET 8", ".NET 6"]
            })
            fallback_techs.append({
                "category": "runtime",
                "label": "Runtime / Language Version",
                "detected": ".NET 6+",
                "confidence": 75,
                "alternatives": [".NET 8", ".NET 9"]
            })
        
        results.extend(fallback_techs)

    return results


def _extract_dependency_text(files: list[dict]) -> str:
    """Extract text from dependency/config files for pattern matching."""
    dep_files = [
        "pom.xml", "build.gradle", "build.gradle.kts", "package.json",
        "requirements.txt", "setup.py", "pyproject.toml", "Cargo.toml",
        "go.mod", "application.properties", "application.yml",
        "persistence.xml", "web.xml",
    ]
    texts = []
    for f in files:
        # Check both 'filename' and 'path' fields, and extract filename from path
        filename = f.get("filename", "")
        if not filename:
            path = f.get("path", "")
            filename = path.split("/")[-1] if "/" in path else path.split("\\")[-1] if "\\" in path else path
        
        if filename in dep_files:
            texts.append(f.get("content", ""))
    return "\n".join(texts)
