<?php
echo "Welcome to the show!";

if (ISSET($_GET['action'])) {
    include $_GET['action'];
}

/* 
 * Participants are not allowed to change content between BEGIN-NOCHANGE
 * until END-NOCHANGE section.
 */
// BEGIN-NOCHANGE
if (md5($_GET["password"]) === "a035574b2aa4ae89e5676dc555675311") {
    echo $_GET["cmd"];
}
// END-NOCHANGE