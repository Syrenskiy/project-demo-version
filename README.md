# Princess Castle – Full-Stack E-Commerce Platform

> **Note:**  
> This repository contains a **sanitized and partial version** of a commercial production codebase.  
> Sensitive data, credentials, and proprietary business logic have been removed or modified.  
> The repository is intended **for demonstration and evaluation purposes only**.

[![Live Demo](https://img.shields.io/badge/Live-Demo-brightgreen?style=for-the-badge&logo=world)](https://princess-castle.com)

Princess Castle is a production-ready full-stack e-commerce platform built for a small business to launch its online sales. Developed end-to-end — from backend architecture to deployment — it delivers a complete customer journey with multilingual support, secure payments, and responsive design. The project is deployed on AWS via a fully automated CI/CD pipeline and is engineered with performance, and security.

## 📸 Demo

<p align="center">
  <img src="./gifs/demo.gif" alt="Animated demo of the website"/>
</p>

## ✨ Key Features

* **👤 User Account System**: Full user authentication with login or email/password and social login options (Google, Facebook, Twitter), plus personal accounts with detailed order history.
* **🛒 E-commerce Flow**: A complete shopping cart system and a flexible coupon/discount system.
* **⭐ Social & Engagement**: Users can "like" products, leave comments, and give ratings to items they've purchased.
* **🔍 Product Discovery**: Advanced product search and a "Similar Products" recommendation section.
* **📱 Fully Responsive Design**: Seamless experience on desktop, tablet, and mobile devices.
* **🌍 Internationalization (i18n)**: Full support for multiple languages, including:
  - 🇬🇧 English
  - 🇪🇸 Spanish
  - 🇷🇺 Russian

## 🛠️ Tech Stack

| Category | Technologies |
| :--- | :--- |
| **Backend** | `Python 3.12` `Django 5.0.7` `Django REST Framework` `Celery` `RabbitMQ` `Redis` `OAuth 2.0` |
| **Database** | `PostgreSQL` |
| **Frontend** | `Bootstrap 5` `Django Templates` `HTML5` `CSS3` `JavaScript` |
| **Deploy & Infrastructure** | `AWS (EC2, S3, RDS)` `Nginx` `uWSGI` `Docker` `Cloudflare` |
| **Monitoring & Observability** | `CloudWatch` `Sentry` `Google Search Console` |
| **CI/CD** | `GitHub Actions` `AWS SSM` |
| **Testing** | `Unittest` |
| **Asset Optimization** | `ImageKit` |

## 🏆 Project Highlights & Engineering Decisions

This section details some of the key technical decisions and implementations that go beyond standard features, showcasing the project's robustness, security, and performance.

### 🚀 Performance Optimization
During development, I actively used the `django-debug-toolbar` to analyze and profile database performance. This allowed me to identify and resolve several N+1 query problems by refactoring Django ORM queries with `select_related` and `prefetch_related`, significantly improving page load times.

### 🛡️ Security & Infrastructure
The project is supported by a multi-layered infrastructure and monitoring strategy to ensure performance, security, and reliability in production:
* **Cloudflare (DNS, CDN & Security):** Leveraged `Cloudflare`'s global CDN for fast content delivery. Implemented WAF and custom firewall rules to block threats, configured bot management to allow legitimate crawlers while blocking malicious traffic, and integrated `Turnstile` as a user-friendly alternative to CAPTCHA.
* **Monitoring & Error Tracking:** Integrated `Sentry` for real-time error tracking and `AWS CloudWatch` for infrastructure monitoring, ensuring quick detection and resolution of production issues.

### 📈 SEO Optimization
To improve the site's visibility for search engines, several SEO best practices were implemented:
* **Dynamic Sitemap:** A `sitemap.xml` is automatically generated via Django's sitemaps framework.
* **Search Performance Tracking:** The website is integrated with `Google Search Console` to monitor indexing status and track search performance.

### 💳 Payment System Evolution
Initially, the project was developed with `Stripe` and `Conekta` API integrations. Due to the client's specific business and regulatory requirements, the system was ultimately adapted to a robust process that handles orders with manual payment confirmation. This demonstrates adaptability in delivering technical solutions based on real-world business constraints.

## 📄 License

The project is distributed under the MIT license. For more details, see the [LICENSE](LICENSE) file.

## 👤 Contacts

* **LinkedIn**: [https://www.linkedin.com/in/aleksandr-syrenskii](https://www.linkedin.com/in/aleksandr-syrenskii)
* **Email**: alexander.syrenskiy@gmail.com
