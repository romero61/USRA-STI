

# USRA-STI

Providing a Keras CNN machine learning approach to estimate P.M.
2.5 levels, utilizing Google Earth Engine's MERRA-2 Data

A web app version can be found on:

<a href="https://huggingface.co/spaces/romero61/USRA-STI"><img src="https://raw.githubusercontent.com/romero61/romero61.github.io/main/img/hf-logo.png" alt="HF Logo" style="width: 125px;"/></a>

# TOC

-   [Understanding the Repository Contents](#understanding-the-repository-contents)
-   [Using the Jupyter Notebook Locally](#using-the-jupyter-notebook-locally)
-   [Using the Jupyter Notebook with Google Colab](#using-the-jupyter-notebook-with-google-colab)
-   [Notes](#notes)

# Understanding the Repository Contents: {#understanding-the-repository-contents}

#### Overview

The application developed during the internship at the Universities Space Research Association (USRA) represents a significant advancement in leveraging geospatial data for environmental analysis.
The project's core is an interactive web application designed to analyze, visualize, and interpret air quality data, particularly PM2.5 levels, using data from Google Earth Engine (GEE) and advanced machine learning techniques through Convolutional Neural Networks (CNNs).
The application integrates sophisticated data preprocessing, machine learning models provided by USRA, and a user-friendly interface for comprehensive environmental data analysis.

The application developed during the USRA internship represents a blend of advanced data processing techniques, machine learning, and interactive web technologies.
It stands as a testament to the power of interdisciplinary approaches in solving environmental challenges.
By making complex geospatial and environmental data accessible and understandable, the application aids in raising awareness, guiding policy decisions, and fostering scientific curiosity and research in air quality and environmental science.

![](notebook.png)

# Components and Architecture

1.  **Data Preprocessing and CNN Models (Provided by USRA):**

    -   **Preprocessing Scripts:** Scripts to fetch and preprocess geospatial data from Earth Engine, including aerosol and meteorological variables.
        The preprocessing involves data normalization, feature extraction, and preparation for CNN input.

    -   **CNN Models:** Advanced machine learning models developed to estimate PM2.5 levels from satellite imagery and other geospatial data.
        These models are trained on historical data and can predict air quality indicators, providing insights into environmental conditions.

2.  **Interactive Web Application:**

    -   **Frontend UI Components:**

        -   Developed using modern web technologies and libraries to create a responsive and interactive user interface.

        -   Components include date range selectors, map visualization tools, and options to choose different types of data visualizations and analyses.

    -   **Integration with Earth Engine:**

        -   Utilizes the Google Earth Engine's Python API for data retrieval and processing.
            The application queries GEE for specific datasets related to air quality and environmental conditions.

        -   Enables dynamic data visualization based on user-selected parameters, such as date ranges, regions, and specific environmental variables.

    -   **Visualization and Analysis:**

        -   Implements various visualization tools, including contour plots, heatmaps, and Earth Engine images, to represent the data effectively.

        -   Allows users to interact with the data, select specific time frames, regions, and view detailed environmental information graphically.

#### Development Environment and Technologies

-   **Python and Jupyter Environment:** The application's backend and data processing components are developed in Python, leveraging libraries like NumPy, Pandas, Matplotlib, and specifically Earth Engine's Python API for geospatial data manipulation.

-   **Geospatial Libraries:** Utilizes **`geemap`**, **`ee`**, and **`cartopy`** for mapping and spatial data visualization.

-   **Web Technologies:** Employs libraries like **`solara`**, **`reacton.ipyvuetify`**, and **`ipywidgets`** for creating interactive web components and layouts.

-   **Deployment and Accessibility:** The application is made accessible as a web-based tool, possibly hosted on platforms like Hugging Face Spaces, allowing users to interact with the application through a web browser without needing any local setup.

# Using the Jupyter Notebook Locally {#using-the-jupyter-notebook-locally}

1.  Clone the Repository: Clone the repository to your local machine using Git.
    In your terminal or command prompt, run: `git clone https://github.com/romero61/USRA-STI.git` This will create a copy of the repository on your computer.

2.  Install Required Dependencies: Navigate to the cloned repository directory.
    If there is a requirements.txt file, you can install the required Python packages using pip: `pip install -r requirements.txt`

3.  Open the Jupyter Notebook: If you have Jupyter installed, you can launch it by typing `jupyter notebook` in your terminal or command prompt.
    Navigate to the notebook file (`.ipynb`) within the Jupyter interface and open it.

# Using the Jupyter Notebook with Google Colab {#using-the-jupyter-notebook-with-google-colab}

1.  Open Google Colab: Go to [Google Colab](https://colab.research.google.com/).

2.  Import the Notebook: In Colab, choose 'File' \> 'Open notebook'.
    Select the 'GitHub' tab.
    Enter the repository URL (<https://github.com/romero61/USRA-STI>) and search.
    Click on the notebook file from the search results to open it in Colab.

3.  Install Any Required Packages: If the notebook requires specific Python packages not available in Colab by default, you can install them directly in a notebook cell using `!pip install package-name`.

4.  Run the Notebook: You can now run the notebook cells one by one.
    If the notebook uses external files (like datasets), you might need to upload them to Colab or modify the notebook to read them from a cloud storage like Google Drive.

# Notes: {#notes}

Jupyter Notebooks: These are interactive documents containing live code, equations, visualizations, and narrative text.
They are widely used for data cleaning and transformation, numerical simulation, statistical modeling, data visualization, machine learning, and much more.
Local vs. Colab: Running the notebook locally requires setting up a Python environment and Jupyter Notebook on your machine.
Google Colab, on the other hand, provides a ready-to-use environment with most common libraries pre-installed and offers free access to GPUs and TPUs for computation.
GitHub Repository: The repository is a source for all the necessary files and often includes instructions or documentation on how to use them.
Always check for a README.md file for specific instructions related to the repository.

# References

For assistance please feel free to reach out: [Guillermo Romero](https://github.com/romero61)

-   ["GESDISC." Nasa.gov, 2023](https://disc.gsfc.nasa.gov/information/mission-project?title=HAQAST:%20Global%20Daily%20PM2.5)

-   Global Modeling and Assimilation Office (GMAO) (2015), *inst3_3d_asm_Cp: MERRA-2 3D IAU State, Meteorology Instantaneous 3-hourly (p-coord, 0.625x0.5L42), version 5.12.4*, Greenbelt, MD, USA: Goddard Space Flight Center Distributed Active Archive Center (GSFC DAAC), doi: 10.5067/VJAFPLI1CSIV.

-   Wu, Q., (2020).
    geemap: A Python package for interactive mapping with Google Earth Engine.
    The Journal of Open Source Software, 5(51), 2305.
    <https://doi.org/10.21105/joss.02305>

-   Wu, Q., Lane, C. R., Li, X., Zhao, K., Zhou, Y., Clinton, N., DeVries, B., Golden, H. E., & Lang, M. W.
    (2019).
    Integrating LiDAR data and multi-temporal aerial imagery to map wetland inundation dynamics using Google Earth Engine.
    Remote Sensing of Environment, 228, 1-13.
    <https://doi.org/10.1016/j.rse.2019.04.015> ([pdf](https://gishub.org/2019_rse) \| [source code](https://doi.org/10.6084/m9.figshare.8864921))

# 

License This project is licensed under the MIT License - see the LICENSE.md file for details
