#!/usr/bin/env python3
import cmd
import sys

class WardenCLI(cmd.Cmd):
    intro = "\n🔷 Agentic Warden CLI 🔷\n"
    prompt = "(warden) "

    def do_approve(self, arg):
        if not arg:
            print("Usage: approve <id>")
            return
        print(f"✅ Approved {arg}")

    def do_reject(self, arg):
        print(f"❌ Rejected {arg}")

    def do_revoke(self, arg):
        print("🔴 REVOKING AGENTIC WARDEN")
        sys.exit(0)

    def do_exit(self, arg):
        return True

if __name__ == "__main__":
    WardenCLI().cmdloop()
