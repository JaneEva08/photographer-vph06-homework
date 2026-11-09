if (location.pathname.startsWith("/admin")) {
  import("./admin.js");
} else {
  import("./site.js");
}
