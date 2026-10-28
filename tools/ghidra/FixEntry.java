// Import-time fixup for stripped binaries: auto-analysis often leaves main (passed to
// __libc_start_main from entry) as a bare label, so its strings/xrefs are never attached.
// Create a function at every code address referenced from entry point functions, then re-analyze.
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressIterator;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.symbol.*;

public class FixEntry extends GhidraScript {
    @Override
    public void run() throws Exception {
        FunctionManager fm = currentProgram.getFunctionManager();
        int created = 0;
        AddressIterator eps = currentProgram.getSymbolTable().getExternalEntryPointIterator();
        while (eps.hasNext()) {
            Function ep = fm.getFunctionAt(eps.next());
            if (ep == null) continue;
            for (Instruction ins : currentProgram.getListing().getInstructions(ep.getBody(), true)) {
                for (Reference r : ins.getReferencesFrom()) {
                    Address to = r.getToAddress();
                    MemoryBlock b = currentProgram.getMemory().getBlock(to);
                    if (b == null || !b.isExecute() || fm.getFunctionContaining(to) != null) continue;
                    disassemble(to);
                    if (createFunction(to, null) != null) {
                        println("FixEntry: created function at " + to + " (referenced from " + ep.getName() + ")");
                        created++;
                    }
                }
            }
        }
        if (created > 0) analyzeAll(currentProgram);
    }
}
