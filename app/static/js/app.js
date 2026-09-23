/**
 * GeoAttend Pro — app.js
 *
 * Batch 1 scope only: no GPS, no forms, no API calls yet.
 * This file just wires up small UI behaviors that don't need the backend.
 * Later batches (Sign-In / Sign-Out) will add navigator.geolocation calls
 * that POST straight to Flask routes — not to an API layer.
 */

(function () {
  "use strict";

  function initFlashDismiss() {
    // Batch 14: flashes still dismiss on click, but now also auto-dismiss
    // like a toast so an employee standing at the gate doesn't have to tap
    // anything after a sign-in/sign-out message appears.
    var AUTO_DISMISS_MS = 5000;

    document.querySelectorAll(".flash").forEach(function (flash) {
      var timer = window.setTimeout(function () {
        fadeAndRemove(flash);
      }, AUTO_DISMISS_MS);

      flash.addEventListener("mouseenter", function () {
        window.clearTimeout(timer);
      });

      var dismissBtn = flash.querySelector(".flash__dismiss");
      if (dismissBtn) {
        dismissBtn.addEventListener("click", function () {
          window.clearTimeout(timer);
          fadeAndRemove(flash);
        });
      }
    });
  }

  function fadeAndRemove(el) {
    el.style.transition = "opacity 0.2s ease";
    el.style.opacity = "0";
    window.setTimeout(function () {
      el.remove();
    }, 200);
  }

  function initAdminMobileNav() {
    // Batch 14 fix: the admin sidebar used to just disappear at ≤780px with
    // no way to reopen it. Now a hamburger button toggles it as an
    // off-canvas drawer, with a tap-outside backdrop to close it again.
    var toggle = document.getElementById("admin-nav-toggle");
    var sidebar = document.querySelector(".admin-sidebar");
    var backdrop = document.getElementById("admin-sidebar-backdrop");

    if (!toggle || !sidebar || !backdrop) {
      return;
    }

    function openNav() {
      sidebar.classList.add("is-open");
      backdrop.classList.add("is-open");
      toggle.setAttribute("aria-expanded", "true");
    }

    function closeNav() {
      sidebar.classList.remove("is-open");
      backdrop.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
    }

    toggle.addEventListener("click", function () {
      if (sidebar.classList.contains("is-open")) {
        closeNav();
      } else {
        openNav();
      }
    });

    backdrop.addEventListener("click", closeNav);

    // Closing on nav-link tap keeps the drawer from staying open when the
    // employee/admin navigates to the next page on a slow connection.
    sidebar.querySelectorAll(".admin-nav__link, .admin-sidebar__logout").forEach(function (link) {
      link.addEventListener("click", closeNav);
    });

    window.addEventListener("resize", function () {
      if (window.innerWidth > 780) {
        closeNav();
      }
    });
  }

  function initAdminLiveSearch() {
    var searchInput = document.getElementById("global-admin-search") || document.querySelector(".admin-search__input");
    if (!searchInput) return;

    searchInput.addEventListener("input", function () {
      var query = this.value.toLowerCase().trim();
      var rows = document.querySelectorAll("table.table tbody tr");
      rows.forEach(function (row) {
        var text = row.textContent.toLowerCase();
        if (query === "" || text.indexOf(query) !== -1) {
          row.style.display = "";
        } else {
          row.style.display = "none";
        }
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initFlashDismiss();
    initAdminMobileNav();
    initAdminLiveSearch();
  });
})();
