var newsanta = newsanta || {};

newsanta.BLUR_RADIUS = 8;

newsanta.CanvasBackend = function(options) {
  snowmachine.CanvasBackend.call(this, options);

  this.blur = options.blur || [];
};

newsanta.CanvasBackend.prototype = Object.create(snowmachine.CanvasBackend.prototype);

newsanta.CanvasBackend.prototype.render = function(snowflakes) {
  var canvas = this.canvas.id;

  snowmachine.CanvasBackend.prototype.render.call(this, snowflakes);

  this.blur.forEach(function(region) {
    stackBlurCanvasRGBA(canvas, region.x, region.y, region.width,
                        region.height, newsanta.BLUR_RADIUS);
  });
};
