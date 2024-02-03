from setuptools import find_packages, setup

setup(
    name="edu-lark-bot",
    author="roostinghawk",
    author_email="roostinghawk@163.com",
    url="https://github.com/roostinghawk/edu-lark-bot",
    license="MIT",
    version="2.3.0",
    description="edu-lark-bot",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["PyGithub", "requests", "pendulum"],
    entry_points={
        "console_scripts": ["edu-lark-bot = github_daily.cli:main"],
    },
)
