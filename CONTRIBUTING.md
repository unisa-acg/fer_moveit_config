# Contribution guidelines

## Branching model

The branching model used in this repository is [GitFlow](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow).

### Branch types

This model foresees a set of well known branch names and types.
These are:

* **master**: This branch is an ever lasting branch that includes all released software versions
* **develop**: This branch is an ever lasting branch that includes all working and deployable software
* **feature**: This is a branch category (`feature/<branch_name>`) that is used when the developer is adding a new functionality.
    This includes refactorings that are aimed to make software more maintainable and extendable.
* **bugfix**: This is a branch category (`bugfix/<branch_name>`) that is aimed to solve a bug and branches out from develop.
* **hotfix**: This is a branch category (`hotfix/<branch_name>`) that is aimed to solve a bug that is found on released software (on the master branch).
* **release**: This is a branch category (`release/<branch_name>`) that is aimed to freeze the baseline for a software release that will be merged to the master branch. This branch family branches out from the develop.

**Branch scope**: branch scopes should be limited and focused as much as possible to accomplish a specific goal.

**Branch names**: branches should be named after their goal.
Their name should not exceed 4 words and should be in [snake case](https://it.wikipedia.org/wiki/Snake_case).

### Branching dynamics

As part of the gitflow workflow there is a scheme that shall be followed when forking and merging the branch types mentioned before:

* **master**: starts from the root of the tree, it is the main development branch therefore it is not merged into other branches
* **develop**: branches off from master very early in the git log, it merges back into master indirectly through a release branch
* **feature**: are created from develop or from other feature branches and merge back on develop.
    It is suggested to branch from feature branches only temporarily until the feature branch is merged into develop.
* **bugfix**: follows the same branching pattern of feature branches
* **hotfix**: branches off from master and merges back to master.
* **release**: branches off from develop and merges both into master and develop

### Development and review workflow

1. Identify your bugfix or feature and **agree a branch name** `<name>` with a repository administrator.
1. Identify the branch to start from, either `develop` or another feature or bugfix branch.
1. Develop your feature or bugfix and their tests, **write its documentation** (typically a user manual, important maintenance information and known issues, if any)
1. **Execute tests** (unless they are automatically executed) and review the documentation
1. Upon successful tests, request the merge of the branch onto the `develop` through opening a **Pull Request (PR)**.
    PRs officially start the review process.
1. Reviewers generate comments requiring modifications of the source code, test code, configuration and/or documentation.
1. Discuss with reviewers through the PR and implement their comments.
1. Upon implementation of comments, reviewers approve the PR or request further changes.
1. Upon reviewers approvals, administrators merge the feature or bugfix branch onto the `develop`.

## Commit messages

Configure git for using the .gitmessage as commit template issuing the following command:

```bash
git config commit.template .gitmessage
```

this command configures git to use this template only for this project, if you like to configure git to use it for all project you should add the global flag as follows:

```bash
git config --global commit.template ~/.gitmessage
```

When writing commit messages, please use the following conventions

* ADD adding new feature
* FIX a bug
* DOC documentation only
* REF refactoring that doesn't include any changes in features
* FMT formatting only (spacing...)
* MAK repository related changes (e.g., changes in the ignore list)
* TST related to test code only

Use bullet lists for commits including more than one change.
See the latest commit messages for an example before making your first commit!

## Coding standards

The aim of this section is to help you configure your development node to produce code aligned with the coding standards adopted by the project.

### Install pre-commit

At the time of writing this documentation, aptitude (`sudo apt install`) installs

```bash
nodeenv     v0.13.4
pre-commit  v3.6.2
```

If, in your system, `nodeenv` and `pre-commit` are at a newer version, move to the [next section](#configure-hooks).

This `nodeenv` version `0.13.4` does not comply with hooks at [https://github.com/tier4/pre-commit-hooks-ros](https://github.com/tier4/pre-commit-hooks-ros). In order to use them, please install an automatically-managed virtual environment with `pipx`:

```bash
sudo apt install pipx
pipx install nodeenv
pipx install pre-commit
```

Now, make sure these versions are reached instead of system ones through

```bash
echo 'export PATH="/home/$USER/.local/bin:$PATH"' >> ~/.bashrc
```

Do not use `pipx ensurepath` because this will append your `~/.local/bin` to your `PATH` and will be masked by the system path.

Open a new terminal and run

```bash
nodeenv --version
pre-commit --version
```

These should return newer versions with respect to above.

### Configure hooks

Depending on already installed packages, some additional dependencies might be needed by the configured hooks:

```bash
sudo apt install ruby shellcheck clang-format
```

Make sure that pre-commit runs correctly in your repo:

```bash
pre-commit run --all-files
```

For more details on pre-commit see the [official documentation](https://pre-commit.com/).

Finally, install the git pre-commit hook that will execute pre-commit at each new commit.

```bash
pre-commit install
```

From now on, at each new commit, `pre-commit` will be executed to make sure that your code is aligning to the adopted coding standards.
