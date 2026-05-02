# macOS Signing and Loader Caveats

- Apple Silicon requires native arm64 code to have at least an ad hoc signature.
- `LC_CODE_SIGNATURE` points to an embedded SuperBlob containing a CodeDirectory.
- `codesign --verify` proves the signature is structurally valid on disk; it does not prove release XNU will execute static non-dyld arm64 `MH_EXECUTE`.
- Release XNU rejects static `MH_EXECUTE` binaries except x86_64. For arm64, generate dynamic runnable alternatives when execution matters.
- `LC_UNIXTHREAD` is useful for research artifacts; `LC_MAIN` implies dyld.
