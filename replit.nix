{ pkgs }: {
  deps = [
    pkgs.ffmpeg
    pkgs.python311Full
    pkgs.replitPackages.prybar-python311
    pkgs.replitPackages.stderred
  ];
  env = {
    PYTHON_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      pkgs.ffmpeg
      pkgs.stdenv.cc.cc.lib
      pkgs.zlib
    ];
    PYTHONHOME = "${pkgs.python311Full}";
    PYTHONBIN = "${pkgs.python311Full}/bin/python3.11";
    LANG = "en_US.UTF-8";
    STDERREDBIN = "${pkgs.replitPackages.stderred}/bin/stderred";
    PRYBAR_PYTHON_BIN = "${pkgs.replitPackages.prybar-python311}/bin/prybar-python311";
    PRYBAR_PYTHON_LIBRARY_PATH = "${pkgs.replitPackages.prybar-python311}/lib";
  };
}
