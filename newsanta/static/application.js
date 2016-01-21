$(function() {
  setTimeout(function() {
    var blur = [];
    var canvas = document.getElementById('profile-snow');

    if (!canvas) {
      canvas = document.getElementById('welcome-snow');
      canvas.height = 560;
    } else {
      canvas.height = 887;
      blur = [
        {
          x: window.innerWidth / 2 - 470,
          y: 203,
          width: 460,
          height: 545
        },
        {
          x: window.innerWidth / 2 + 10,
          y: 203,
          width: 460,
          height: 545
        }
      ];
    }

    canvas.width = window.innerWidth;

    var backend = new newsanta.CanvasBackend({
      element: canvas,
      blur: blur
    });

    var engine = new snowmachine.SimpleEngine({
      backend: backend,
      count: 150
    });

    engine.start();
  }, 2000);
});
