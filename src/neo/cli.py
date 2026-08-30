from __future__ import annotations

import argparse
import getpass
import json
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

from neo.agent import ActionExecutor, ActionRequest, ActionType, PermissionScope
from neo.bootstrap import bootstrap
from neo.device import DeviceProfiler
from neo.discovery import DiscoveryPolicy, SilentDiscovery
from neo.drive import DriveManager, VaultArchive
from neo.learning import LearningEngine
from neo.memory import MemoryKind
from neo.people import PeopleEngine
from neo.product import ProductSession, check_product_health
from neo.projects import ProjectDetector
from neo.screen import ScreenIntelligence


def _json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="neo", description="NEO Phase 1 core CLI")
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("status", help="show hardware, selected model, storage and Ollama status")
    commands.add_parser("device", help="capture and save the current machine profile")
    commands.add_parser("doctor", help="check whether NEO is product-ready on this host")
    session = commands.add_parser("session", help="portable host identity and consent")
    session_commands = session.add_subparsers(dest="session_command", required=True)
    session_commands.add_parser("identify")
    session_revoke = session_commands.add_parser("revoke")
    session_revoke.add_argument("machine_id")
    discovery = commands.add_parser("discover", help="permission-gated local discovery")
    discovery.add_argument("roots", nargs="+", type=Path)
    discovery.add_argument("--grant", action="store_true", help="explicitly grant these roots")
    discovery.add_argument("--metadata-only", action="store_true")
    discovery.add_argument("--max-files", type=int, default=20_000)
    people = commands.add_parser("people", help="people profile operations")
    people_commands = people.add_subparsers(dest="people_command", required=True)
    person_add = people_commands.add_parser("add")
    person_add.add_argument("name")
    person_add.add_argument("--alias", action="append", default=[])
    people_commands.add_parser("list")
    people_commands.add_parser("propose-owner")
    person_import = people_commands.add_parser("import-vcard")
    person_import.add_argument("path", type=Path)
    person_find = people_commands.add_parser("find")
    person_find.add_argument("name")
    projects = commands.add_parser("projects", help="detect projects and project skills")
    projects.add_argument("roots", nargs="+", type=Path)
    projects.add_argument("--max-depth", type=int, default=6)
    screen = commands.add_parser("screen", help="consent-gated screen intelligence")
    screen_commands = screen.add_subparsers(dest="screen_command", required=True)
    screen_commands.add_parser("grant")
    screen_commands.add_parser("revoke")
    screen_commands.add_parser("app")
    screen_analyze = screen_commands.add_parser("analyze")
    screen_analyze.add_argument("question")
    screen_analyze.add_argument("--monitor", type=int, default=1)
    agent = commands.add_parser("agent", help="typed permission-gated system actions")
    agent_commands = agent.add_subparsers(dest="agent_command", required=True)
    agent_grant = agent_commands.add_parser("grant")
    agent_grant.add_argument("action", choices=[item.value for item in ActionType])
    agent_grant.add_argument("scope", choices=[item.value for item in PermissionScope])
    agent_grant.add_argument("--target")
    agent_run = agent_commands.add_parser("run")
    agent_run.add_argument("action", choices=[item.value for item in ActionType])
    agent_run.add_argument("--target")
    agent_run.add_argument("--arguments", default="{}", help="JSON object")
    agent_undo = agent_commands.add_parser("undo")
    agent_undo.add_argument("action_id")
    learning = commands.add_parser("learn", help="controlled learning and skill evolution")
    learning_commands = learning.add_subparsers(dest="learn_command", required=True)
    correction = learning_commands.add_parser("correct")
    correction.add_argument("subject")
    correction.add_argument("wrong")
    correction.add_argument("correct")
    failure = learning_commands.add_parser("failure")
    failure.add_argument("subject")
    failure.add_argument("error")
    failure.add_argument("--action", required=True)
    learning_commands.add_parser("consolidate")
    drive = commands.add_parser("drive", help="backup, encrypted export and migration")
    drive_commands = drive.add_subparsers(dest="drive_command", required=True)
    drive_commands.add_parser("status")
    drive_backup = drive_commands.add_parser("backup")
    drive_backup.add_argument("destination", type=Path)
    drive_export = drive_commands.add_parser("export")
    drive_export.add_argument("destination", type=Path)
    drive_import = drive_commands.add_parser("import")
    drive_import.add_argument("archive", type=Path)
    drive_import.add_argument("destination", type=Path)
    drive_migrate = drive_commands.add_parser("migrate")
    drive_migrate.add_argument("destination", type=Path)
    memory = commands.add_parser("memory", help="persistent memory operations")
    memory_commands = memory.add_subparsers(dest="memory_command", required=True)
    set_command = memory_commands.add_parser("set")
    set_command.add_argument("key")
    set_command.add_argument("value", help="JSON value or plain text")
    set_command.add_argument(
        "--kind", choices=[item.value for item in MemoryKind], default="learned"
    )
    set_command.add_argument("--confidence", type=float, default=1.0)
    set_command.add_argument("--source")
    set_command.add_argument("--protect", action="store_true")
    set_command.add_argument("--ttl", type=int)
    get_command = memory_commands.add_parser("get")
    get_command.add_argument("key")
    list_command = memory_commands.add_parser("list")
    list_command.add_argument("--limit", type=int, default=100)
    list_command.add_argument("--kind", choices=[item.value for item in MemoryKind])
    search_command = memory_commands.add_parser("search")
    search_command.add_argument("query")
    search_command.add_argument("--limit", type=int, default=20)
    delete_command = memory_commands.add_parser("delete")
    delete_command.add_argument("key")
    delete_command.add_argument("--force", action="store_true")
    relate_command = memory_commands.add_parser("relate")
    relate_command.add_argument("source_key")
    relate_command.add_argument("relation")
    relate_command.add_argument("target_key")
    relate_command.add_argument("--confidence", type=float, default=1.0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    runtime = bootstrap()
    if args.command in (None, "status"):
        ollama = runtime.ollama.status()
        _json(
            {
                "hardware": runtime.hardware.to_dict(),
                "model": asdict(runtime.model),
                "storage": {**asdict(runtime.storage), "path": str(runtime.storage.path)},
                "ollama": asdict(ollama),
            }
        )
        return 0
    if args.command == "memory":
        if args.memory_command == "set":
            try:
                value = json.loads(args.value)
            except json.JSONDecodeError:
                value = args.value
            _json(
                asdict(
                    runtime.memory.set(
                        args.key,
                        value,
                        kind=args.kind,
                        confidence=args.confidence,
                        source=args.source,
                        protected=args.protect,
                        ttl_seconds=args.ttl,
                    )
                )
            )
        elif args.memory_command == "get":
            entry = runtime.memory.get(args.key)
            if entry is None:
                return 1
            _json(asdict(entry))
        elif args.memory_command == "list":
            _json([asdict(item) for item in runtime.memory.list(args.limit, kind=args.kind)])
        elif args.memory_command == "search":
            _json([asdict(item) for item in runtime.memory.search(args.query, args.limit)])
        elif args.memory_command == "delete":
            _json({"deleted": runtime.memory.forget(args.key, force=args.force)})
        elif args.memory_command == "relate":
            _json(
                asdict(
                    runtime.memory.relate(
                        args.source_key,
                        args.relation,
                        args.target_key,
                        confidence=args.confidence,
                    )
                )
            )
        return 0
    if args.command == "device":
        profiler = DeviceProfiler()
        profile = profiler.capture()
        saved = profiler.save(profile, runtime.storage.path / "profiles" / "machines")
        _json({"saved_to": str(saved), "profile": profile.to_dict()})
        return 0
    if args.command == "doctor":
        health = check_product_health(runtime)
        _json({"ready": health.ready, "checks": [asdict(item) for item in health.checks]})
        return 0 if health.ready else 1
    if args.command == "session":
        product_session = ProductSession(runtime)
        if args.session_command == "identify":
            profile = product_session.identify_host()
            _json(
                {
                    "profile": profile.to_dict(),
                    "consent": (
                        asdict(consent)
                        if (consent := product_session.consent_for(profile.machine_id))
                        else None
                    ),
                }
            )
        elif args.session_command == "revoke":
            _json({"revoked": product_session.revoke(args.machine_id)})
        return 0
    if args.command == "discover":
        service = SilentDiscovery(runtime.memory)
        roots = tuple(args.roots)
        if args.grant:
            service.grant(roots)
        report = service.run(
            DiscoveryPolicy(
                roots,
                max_files=args.max_files,
                allow_content=not args.metadata_only,
            )
        )
        _json(asdict(report))
        return 0
    if args.command == "people":
        engine = PeopleEngine(runtime.memory)
        if args.people_command == "add":
            _json(asdict(engine.create(args.name, aliases=tuple(args.alias))))
        elif args.people_command == "list":
            _json([asdict(profile) for profile in engine.list()])
        elif args.people_command == "propose-owner":
            _json(asdict(engine.propose_owner()))
        elif args.people_command == "import-vcard":
            content = args.path.read_text(encoding="utf-8", errors="replace")
            _json([asdict(profile) for profile in engine.import_vcard(content)])
        elif args.people_command == "find":
            profile = engine.find(args.name)
            if profile is None:
                return 1
            _json(asdict(profile))
        return 0
    if args.command == "projects":
        profiles = ProjectDetector(runtime.memory).discover(tuple(args.roots), args.max_depth)
        _json([asdict(profile) for profile in profiles])
        return 0
    if args.command == "screen":
        screen_service = ScreenIntelligence(runtime.memory)
        if args.screen_command == "grant":
            screen_service.grant()
            _json({"granted": True})
        elif args.screen_command == "revoke":
            screen_service.revoke()
            _json({"granted": False})
        elif args.screen_command == "app":
            _json(asdict(screen_service.active_app()))
        elif args.screen_command == "analyze":
            decision = runtime.router.decision
            answer = screen_service.analyze(
                runtime.ollama,
                decision.model,
                args.question,
                monitor=args.monitor,
                context_size=decision.context_size,
            )
            _json({"answer": answer, "model": decision.model})
        return 0
    if args.command == "agent":
        executor = ActionExecutor(runtime.memory, runtime.storage.path / "backups" / "agent")
        if args.agent_command == "grant":
            grant = executor.permissions.grant(
                args.action, PermissionScope(args.scope), args.target
            )
            _json(asdict(grant))
        elif args.agent_command == "run":
            arguments = json.loads(args.arguments)
            if not isinstance(arguments, dict):
                raise ValueError("--arguments must be a JSON object")
            request = ActionRequest(ActionType(args.action), args.target, arguments)
            _json(
                {"preview": executor.preview(request), "result": asdict(executor.execute(request))}
            )
        elif args.agent_command == "undo":
            _json(asdict(executor.undo(args.action_id)))
        return 0
    if args.command == "learn":
        learning_engine = LearningEngine(runtime.memory)
        if args.learn_command == "correct":
            _json(asdict(learning_engine.correct(args.subject, args.wrong, args.correct)))
        elif args.learn_command == "failure":
            _json(
                asdict(
                    learning_engine.failure(args.subject, args.error, attempted_action=args.action)
                )
            )
        elif args.learn_command == "consolidate":
            _json(learning_engine.consolidate())
        return 0
    if args.command == "drive":
        manager = DriveManager(runtime.storage.path)
        if args.drive_command == "status":
            _json(asdict(manager.storage_report()))
        elif args.drive_command == "backup":
            saved = manager.backup_database(runtime.memory.database, args.destination)
            _json({"saved_to": str(saved)})
        elif args.drive_command == "export":
            password = getpass.getpass("Archive password: ")
            confirmation = getpass.getpass("Confirm password: ")
            if password != confirmation:
                raise ValueError("passwords do not match")
            _json({"saved_to": str(manager.create_encrypted_export(args.destination, password))})
        elif args.drive_command == "import":
            password = getpass.getpass("Archive password: ")
            _json(
                {
                    "restored_to": str(
                        VaultArchive.decrypt_archive(args.archive, args.destination, password)
                    )
                }
            )
        elif args.drive_command == "migrate":
            _json(asdict(manager.migrate(args.destination)))
        return 0
    parser.error("unknown command")
    return 2
