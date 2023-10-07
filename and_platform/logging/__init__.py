import logging

def init_logs(app):
    logger_submissions = logging.getLogger("submissions")
    logger_logins = logging.getLogger("logins")
    logger_services = logging.getLogger("services")

    logger_submissions.setLevel(logging.INFO)
    logger_logins.setLevel(logging.INFO)
    logger_services.setLevel(logging.INFO)

    log_dir = app.config["LOG_FOLDER"]
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logs = {
        "submissions": os.path.join(log_dir, "submissions.log"),
        "logins": os.path.join(log_dir, "logins.log"),
        "services": os.path.join(log_dir, "services.log"),
    }

    try:
        for log in logs.values():
            if not os.path.exists(log):
                open(log, "a").close()

        submission_log = logging.handlers.RotatingFileHandler(
            logs["submissions"], maxBytes=10485760, backupCount=5
        )
        login_log = logging.handlers.RotatingFileHandler(
            logs["logins"], maxBytes=10485760, backupCount=5
        )
        services_log = logging.handlers.RotatingFileHandler(
            logs["services"], maxBytes=10485760, backupCount=5
        )

        logger_submissions.addHandler(submission_log)
        logger_logins.addHandler(login_log)
        logger_services.addHandler(registration_log)
    except IOError:
        pass

    stdout = logging.StreamHandler(stream=sys.stdout)

    logger_submissions.addHandler(stdout)
    logger_logins.addHandler(stdout)
    logger_services.addHandler(stdout)

    logger_submissions.propagate = 0
    logger_logins.propagate = 0
    logger_services.propagate = 0

def log(logger, format, **kwargs):
    logger = logging.getLogger(logger)
    props = {
        "id": session.get("id"),
        "date": time.strftime("%m/%d/%Y %X"),
    }
    props.update(kwargs)
    msg = format.format(**props)
    logger.info(msg)