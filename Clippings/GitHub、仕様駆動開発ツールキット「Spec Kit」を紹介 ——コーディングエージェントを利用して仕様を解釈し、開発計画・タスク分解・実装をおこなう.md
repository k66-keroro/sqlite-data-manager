---
title: "GitHub、仕様駆動開発ツールキット「Spec Kit」を紹介 ——コーディングエージェントを利用して仕様を解釈し、開発計画・タスク分解・実装をおこなう"
source: "https://gihyo.jp/article/2025/09/github-spec-kit"
author:
  - "[[gihyo.jp]]"
published: 2025-09-03
created: 2025-09-04
description: "GitHubは2025年9月2日、コーディングエージェントを利用した仕様駆動開発（Spec-Driven Development）のためのツールキット「Spec Kit」を開発し、公式ブログで紹介した。"
tags:
  - "clippings"
---
GitHubは2025年9月2日、コーディングエージェントを利用した仕様駆動開発  （Spec-Driven Development）  のためのツールキット  「Spec Kit」  を開発し、公式ブログで紹介した。仕様を  「実行可能」  にすることで、開発意図自体をソフトウェア開発の中核に据えることを目指している。

- [Spec-driven development with AI: Get started with a new open source toolkit - GitHub Blog](https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/)
- [spec-kit - GitHub](https://github.com/github/spec-kit)

Spec Kitは、仕様  （Spec）  からソフトウェア開発の計画を作成して、その計画をタスクに分解し実装するためのオープンソースツールキット。これにより、AIコーディングエージェントと協調してソフトウェア開発を効率的におこなえるようになる。

また仕様作成から始めることで、意図  （what）  を明確にし、技術的な計画  （how）  と実装タスクへと段階的に落とし込むプロセスを通すことができるため、曖昧なプロンプトに依存した  「vibe-coding」  の問題点を回避できる。

Spec Kitを使った開発ワークフローは以下の4段階で構成される。

1\. Specify  （仕様作成）

まずプロジェクトの  「what」  と  「why」  を記述し、コーディングエージェントにより詳細な仕様を生成する。仕様はユーザージャーニーや期待する成果を中心に記述し、技術スタックや実装詳細はこの段階では重視しない。具体的には  「誰が使うのか」  「 ⁠そのユーザーが抱える問題は何か」  「 ⁠ユーザーはどのように操作するのか」  「 ⁠成功とみなす基準は何か」  といった問いに答えることが求められている。仕様は生きた成果物として、利用者や要件が変われば更新され、エージェントはその更新を基に後続の生成物を再計算する流れとなる。

2\. Plan  （計画作成）

次に技術的な方向性や制約  （スタック、アーキテクチャ、コンプライアンス要件、性能目標など）  を提供し、コーディングエージェントが実装計画を生成する。ここでは企業で標準化された技術や、レガシーシステムとの統合要件、コンプライアンスやパフォーマンスの目標など、実運用を左右する条件を明確にする必要がある。複数の計画バリエーションを生成して比較することも可能であり、内部ドキュメントや設計パターンをエージェントに与えれば、それらを計画に組み込ませることができる。エージェントはこうした制約を理解した上で、後続のタスク分解や実装指示を生成する。

3\. Tasks  （タスク分解）

仕様と計画を元に、エージェントがレビュー可能な小さなタスクへと分解する。各タスクは独立して実装・  テスト可能な単位とし、エージェントはこれらのタスクを順次  （あるいは並列で）  実装できるようにする。タスクは  「レビュー可能な差分」  を生む小さな単位にすることが重要であり、これは開発者が個々の変更点を短時間で検証できるようにするとともに、エージェントが自らの出力を検証して次の作業に進むための前提にもなる。ブログでは、タスクが独立して実装・  テスト可能であることを強調しており、これによりエージェントは自動的に検証しながら進行できるという。

4\. Implement  （実装と検証）

エージェントがタスクを実装し、開発者はフェーズごとに生成物を検証して次へ進める。各段階には明確なチェックポイントがあり、開発者は仕様や計画を更新して再生成をおこなってもよい。実装フェーズではエージェントが生成するのは大規模なコードの塊ではなく、特定の問題を解決する焦点を絞った機能であることが強調されている。開発者はその機能をレビューして受け入れるか修正指示を出す役割を担う。

Spec Kitは、GitHub CopilotやClaude Code、Gemini CLIといったコーディングエージェントと協調して動作させることができる。

たとえば、プロジェクトを作りたいディレクトリにおいて、uvxを利用して `specify` を実行し、プロジェクト  （ `<PROJECT_NAME>` ）  を初期化する。

```
uvx --from git+https://github.com/github/spec-kit.git specify init <PROJECT_NAME>
```

すると、GitHub Copilot、Claude Code、Gemini CLIのどれを使うかを選択するプロンプトが表示されるので、利用したいエージェントを選ぶ。

![](https://gihyo.jp/assets/images/ICON/2025/2620_github-spec-kit.jpg)

![](https://gihyo.jp/assets/images/article/2025/09/github-spec-kit/github-spec-kit-terminal.jpg)

そうすると、 `<PROJECT_NAME>` のフォルダが作られて、以下のようなファイルが置かれる  （以下はGitHub Copilotを選択した場合⁠ ） ⁠。

```
.github/prompts/tasks.prompt.md
.github/prompts/specify.prompt.md
.github/prompts/plan.prompt.md
memory/constitution_update_checklist.md
memory/constitution.md
scripts/update-agent-context.sh
scripts/setup-plan.sh
scripts/get-feature-paths.sh
scripts/create-new-feature.sh
scripts/common.sh
scripts/check-task-prerequisites.sh
templates/tasks-template.md
templates/spec-template.md
templates/plan-template.md
templates/agent-file-template.md
```

その後、作成されたテンプレートを起点に、エージェントとの対話を通じて仕様と計画を作り上げていく流れになる。

エージェントに `/specify` で  「何を作るのか  （what⁠ ） ⁠」と  「何のために作るのか  （why⁠ ） ⁠」を伝えると、テンプレート  （ `templates/spec-template.md` など）  を参照して初期の仕様草案が生成される。開発者はその草案をレビューして受入基準やエッジケース、必要なテストケースなどを追記し、機能のスコープと期待される振る舞いを確定する。

その際、プロジェクトにおける非交渉的  （non‑negotiable）  な制約  （不変の原則）  や必須のルールを定める `CONSTITUTION.md`  （今回の例では `memory/constitution.md` ）  を事前にカスタマイズしておくことが望ましい。認証、データ保護、ログ方針、コンプライアンス要件などプロジェクト固有のルールを明記するとよい。

技術的な詳細  （使用するスタック、アーキテクチャ、統合要件など）  は続く `/plan` フェーズで指示し、エージェントがそれをもとに実装計画  （ `specs/<feature>/plan.md` や `implementation-details/` 以下の文書）  を生成する。

最後に `/tasks` で仕様と計画を小さな実装単位に分解し、各タスクを順次  （あるいは並列で）  エージェントに実装させていくかたちになる。

なお、ブログではSpec-Driven Developmentが特に有効な3つのシナリオとして、以下のものを挙げている。

- Greenfield  （新規プロジェクト、zero-to-one） : 仕様を起点に開発することで、目的に沿った実装を得やすくする。
- Feature work  （既存システムへの機能追加、N-to-N+1） : 既存のアーキテクチャ制約を計画段階で反映し、自然な統合を目指す。
- Legacy modernization  （レガシーの近代化） : 既存システムのビジネスロジックを仕様として明確化し、再実装を支援する。

現時点においてSpec Kitは仕様駆動開発のための実験プロジェクトであり、ブログやリポジトリでは今後の改善点として、より緊密なVS Code統合の検討、複数実装の比較機能、およびスケール時の課題に関する利用者からのフィードバックを募っている。リポジトリのExperimental goalsには、技術非依存性  （Technology independence⁠ ） ⁠、エンタープライズ制約の組み込み  （Enterprise constraints⁠ ） ⁠、ユーザー中心の開発  （User‑centric development⁠ ） ⁠、および並列実装探索や反復的なワークフロー支援  （parallel implementation exploration and iterative workflows）  が掲げられている。

おすすめ記事

- [![](https://gihyo.jp/assets/images/ICON/2025/2612_gemini-2.5-flash-image_2.png)
	Google⁠ ⁠ 、  一貫性を  維持した  画像編集を  可能に  する  「Gemini 2. 5 Flash Image」  を  リリース
	](https://gihyo.jp/article/2025/08/gemini-2.5-flash-image)
- [![](https://gihyo.jp/assets/images/ICON/2025/2611_ai-news-note-20250821.jpg)
	AIニュースノート⁠ ⁠ ： AGENTS. mdの  採用は  広がる  ？  （VS Code, cline） , Excelの  Copilot関数で  AIを  活用, Claude Codeが  Team⁠ ⁠ ・  Enterpriseプランに  対応など
	](https://gihyo.jp/article/2025/08/22)