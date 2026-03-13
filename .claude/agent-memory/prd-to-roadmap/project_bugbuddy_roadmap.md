---
name: Bug Buddy v1 로드맵 생성
description: 버그버디 프로젝트 v1 로드맵 - 5 Phase, 9주, Python+Streamlit+Claude+Redmine 기술스택, 2026-03-13 시작
type: project
---

버그버디 v1 로드맵을 2026-03-13에 생성함. 5개 Phase (Phase 0~4), 총 9주 계획.

**Why:** 사업팀/운영팀의 레드마인 이슈 구조화 + 개발자 초기 트리아지 시간 단축이 핵심 목표. 해커톤(Hackathon_HJ) 프로젝트로 시작.

**How to apply:**
- Phase 0(스켈레톤) → Phase 1(입력폼+템플릿) → Phase 2(Claude 분석) → Phase 3(코드검색) → Phase 4(Redmine 연동) 순서
- M1(2026-04-03)이 사업팀 즉시 사용 가능한 MVP 시점
- Phase 4(Redmine)는 Should Have - 없어도 기본 기능 동작
- 기술 스택: Python 3.x, Streamlit, Anthropic Claude API (텍스트만), Redmine REST API (read-only)
- customers.json 기반 고객사-코드 매핑, 24개 고객사
