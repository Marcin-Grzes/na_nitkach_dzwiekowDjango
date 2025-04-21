// const autoprefixer = require('gulp-autoprefixer');
// const cleanCSS = require('gulp-clean-css');
// const rename = require('gulp-rename');
// const babel = require('gulp-babel');
// const uglify = require('gulp-uglify');
// const sourcemaps = require('gulp-sourcemaps');
const gulp= require('gulp');
const sass = require('gulp-sass')(require('sass'));
const browserSync = require('browser-sync').create();
const reload = browserSync.reload;

// Ścieżki do plików
const paths = {
  scss: {
    src: 'src/style/**/*.scss',
    dest: 'events/static/css'
  },
}

// Kompilacja SCSS do CSS
function compileScss(){
  return gulp.src(paths.scss.src)
      .pipe(sass().on('error', sass.logError))
      .pipe(gulp.dest(paths.scss.dest))
      .pipe(browserSync.stream());
}

// Obserwowanie zmian w plikach
function watch(done) {
  browserSync.init({
    proxy: "localhost:8000",
    notify: false
  })
  gulp.watch(paths.scss.src, compileScss).on("change", reload);
  done()
}
// Eksport zadań
exports.watch = watch;

// Zadanie domyślne
exports.default = gulp.series(compileScss, watch);