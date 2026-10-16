# GitDoc AI

## Automated Code Analysis and Intelligent Documentation Generation

GitDoc AI is a web application designed to analyze software repositories and automatically generate structured technical documentation. It helps developers understand existing codebases, identify software architectures, explore dependencies, and produce documentation in French.

## Features

### Repository Analysis

- Analyze software repositories using repository URLs.
- Extract project structure, source files, programming languages, and commit information.
- Analyze source code using Abstract Syntax Trees (AST).

### Software Architecture Detection

Automatically identify and evaluate common software architectures, including:

- Model-View-Controller (MVC)
- Model-View-Presenter (MVP)
- Model-View-ViewModel (MVVM)
- Layered Architecture
- Clean Architecture
- Microservices Architecture
- Monolithic Architecture

### Automatic Documentation Generation

- Generate structured technical documentation in French.
- Produce documentation compatible with MkDocs.
- Generate API documentation in OpenAPI and Swagger formats.
- Compare source code before and after transformations.

### Visualization and Analysis

- Visualize project structure and dependencies.
- Explore relationships between software components.
- Display architecture analysis results and scores.

### Analysis History

- Store previous analyses.
- Review historical results through a dashboard.
- Access generated documentation and analysis reports.

## Technologies

- Python for application logic.
- Flask for web application development.
- Ollama for local language model integration.
- Llama 3 for AI-powered analysis and documentation.
- AST for source code analysis.
- MkDocs for technical documentation generation.
- OpenAPI and Swagger for API documentation.
- HTML, CSS, and JavaScript for the user interface.
- Database and ORM technologies for managing analysis history.
- Git for version control.


## Installation

### Prerequisites

Make sure the following tools are installed:

- Python 3
- pip
- Git
- Ollama
- A compatible language model, such as Llama 3

### Clone the Repository

```bash
git clone YOUR_REPOSITORY_URL
cd GitDoc-AI
```

### Create a Virtual Environment

On Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

On Linux or macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Ollama

Download the required language model:

```bash
ollama pull llama3
```

Make sure Ollama is running and that the application uses the correct API endpoint.

### Run the Application

Execute the application using the appropriate entry point. For example:

```bash
python app.py
```

Open the local address displayed in the terminal. The default Flask development address is commonly:

```text
http://127.0.0.1:5000
```

## How It Works

1. The user submits a supported repository URL.
2. The application retrieves and analyzes the repository's source files.
3. AST-based processing extracts structural information from the code.
4. The system evaluates architectural indicators and identifies a potential software architecture.
5. Ollama and Llama 3 assist with code analysis and documentation generation.
6. The application generates technical documentation and API specifications.
7. Analysis results, architecture scores, and dependencies are presented through the interface.
8. Results can be stored and reviewed through the analysis history.

## Project Objectives

GitDoc AI aims to reduce the time required to document software projects, improve codebase understanding, facilitate software maintenance, and automate repetitive documentation tasks.

It also provides developers with insights into software architecture and relationships between project components.

## Future Improvements

- Support for additional programming languages.
- Integration with GitHub, GitLab, and Bitbucket APIs.
- Improved software architecture detection.
- More accurate AI-generated documentation with source references.
- Export to additional documentation formats.
- Automated analysis pipelines and continuous integration.
- Enhanced security, scalability, and performance.

## Author

Balsam Khedri

Software Engineering Student

GitHub: https://github.com/


## Conclusion

GitDoc AI combines static code analysis and artificial intelligence to simplify software repository analysis, architecture identification, and technical documentation generation.
