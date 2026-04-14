document.addEventListener("DOMContentLoaded", () => {
  const track = document.getElementById("marqueeTrack");

  // auto copy
  track.innerHTML += track.innerHTML;
});