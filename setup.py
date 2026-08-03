from setuptools import find_packages, setup

with open("README.md", "r", encoding='utf-8') as fh:
    long_description = fh.read()


def _read_requirements(path):
    with open(path, "r", encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#') and not line.startswith('-r')]


requirements = _read_requirements("./requirements/runtime.txt")

optional_requirements = _read_requirements("./requirements/optional.txt")
agent_requirements = _read_requirements("./requirements/agent.txt")
hhem_requirements = _read_requirements("./requirements/hhem_integration.txt")
litellm_requirements = ["litellm>=1.80.0,<1.87.0"]
retrieval_requirements = _read_requirements("./requirements/retrieval.txt")
# lmdeploy 单独成组：它硬性要求 transformers>=4.56，与 HHEM 需要的 transformers<4.49 冲突，
# 因此不并入 optional/all，避免同一环境内 HHEM 无法加载。需要时单独 pip install dingo-python[lmdeploy]。
lmdeploy_requirements = ["lmdeploy"]


extras_require = {
    'optional': optional_requirements,
    'agent': agent_requirements,
    'hhem': hhem_requirements,
    'litellm': litellm_requirements,
    'retrieval': retrieval_requirements,
    'lmdeploy': lmdeploy_requirements,
    'all': optional_requirements + hhem_requirements + agent_requirements + litellm_requirements + retrieval_requirements,
}


setup(
    name="dingo-python",
    version="2.4.0",
    author="Dingo",
    description="A Comprehensive AI Data Quality Evaluation Tool for Large Models",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MigoXLab/dingo",
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    install_requires=[i.strip() for i in requirements],
    extras_require=extras_require,
    entry_points={
        'console_scripts': [
            'dingo=dingo.run.cli:main',
        ],
    },
    python_requires='>=3.10',
)
