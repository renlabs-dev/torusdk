{
  description = "Torus official Python SDK / CLI";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs?ref=nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          system = system;
          config.allowUnfree = true;
        };
        python = pkgs.python311;
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            # Command runner
            pkgs.just
            # Python
            python
            pkgs.uv
            pkgs.ruff
            pkgs.basedpyright
          ];
        };
        packages = {
          #   torusdk = pkgs.python310Packages.buildPythonApplication rec {
          #     pname = "torusdk";
          #     version = "0.2.4.1";
          #     format = "pyproject";
          #     src = ./.;
          #     nativeBuildInputs = [
          #       pkgs.python310Packages.hatchling
          #     ];
          #     # Dependencies will be managed by UV in development
          #     # For Nix package, we'd need to specify them explicitly
          #     # but for now we focus on the development environment
          #     doCheck = false;
          #   };
          #   default = torusdk;
        };
      });
}
