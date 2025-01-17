.. SODAR Core documentation master file, created by
   sphinx-quickstart on Thu Sep  6 14:50:08 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. _manual-main:

Welcome to the SODAR Core documentation!
========================================

This documentation provides instructions for integration, usage and development
of reusable SODAR Core apps for projects built on the Django web server.

**SODAR** (System for Omics Data Access and Retrieval) is a specialized system
for managing data in omics research projects.

The **SODAR Core** repository containes reusable and non-domain-specific apps
which make up the core of the SODAR system. These apps can be used for any
Django site which wants to make use of one or more of the following features:

- Project-based user access control
- Dynamic app content management
- Advanced project activity logging
- Small file uploading and browsing
- Managing server-side background jobs
- Caching and aggregation of data from external services
- Tracking site information and statistics

Basics of Django site setup and instructions for third party packages used are
considered out of scope for this documentation. Please refer instead to official
documentation of Django and/or the packages in question.

**NOTE:** When viewing this document in GitLab critical content will by default
be missing. Please click "display source" if you want to read this in GitLab.

**NOTE:** To view this document in the rendered form during development, run
``make html`` in the ``docs`` directory of the repository. You can find the
rendered HTML in ``docs/build``. You will have to install system and Python
dependencies, including ones in ``requirements/local.txt`` for this to work. See
:ref:`dev_sodar_core`.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting_started
   app_projectroles
   app_adminalerts
   app_bgjobs
   app_filesfolders
   app_userprofile
   app_siteinfo
   app_sodarcache
   app_taskflow
   app_timeline
   development
   breaking_changes


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
