;
"use strict";
(function (document) {
    const formatter = new Intl.DateTimeFormat(document.documentElement.lang || navigator.language, {
        dateStyle: 'long'
    });
    document.addEventListener("DOMContentLoaded", function () {
        document.querySelectorAll('time').forEach(function (e) {
            var date = new Date(e.getAttribute('datetime'));
            if (isNaN(date.getTime())) return;
            e.innerText = formatter.format(date);
        });
    });
})(document);
