import os

REPOS_DIR = "repos"

CODEQL_LANGUAGES = {
    "cpp": {
        "nombre": "C / C++",
        "exts": {
            ".c",
            ".cpp",
            ".cc",
            ".cxx",
            ".h",
            ".hpp",
            ".hh",
            ".hxx",
        },
    },
    "csharp": {"nombre": "C#", "exts": {".cs"}},
    "go": {"nombre": "Go", "exts": {".go"}},
    "java": {"nombre": "Java / Kotlin", "exts": {".java", ".kt", ".kts"}},
    "javascript": {
        "nombre": "JavaScript / TypeScript",
        "exts": {".js", ".jsx", ".mjs", ".ts", ".tsx"},
    },
    "python": {"nombre": "Python", "exts": {".py"}},
    "ruby": {"nombre": "Ruby", "exts": {".rb"}},
    "swift": {"nombre": "Swift", "exts": {".swift"}},
}