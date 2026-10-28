// Targeted lookup for suspect points found during leanrea triage.
// Args: <outfile> then one or more of: <func name> | 0x<addr> | str:<substring>
// For each resolved function: signature, callers (with call sites), callees, decompiled C.
// str: resolves every function that references a defined string containing the substring.
import ghidra.app.decompiler.*;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.data.StringDataInstance;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import java.io.PrintWriter;
import java.util.*;

public class Query extends GhidraScript {
    private DecompInterface di;
    private PrintWriter out;

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        out = new PrintWriter(args[0]);
        di = new DecompInterface();
        di.openProgram(currentProgram);
        Set<Function> seen = new LinkedHashSet<>();
        for (String q : Arrays.copyOfRange(args, 1, args.length)) {
            List<Function> fs = resolve(q);
            if (fs.isEmpty()) out.println("QUERY " + q + ": not found");
            for (Function f : fs)
                if (seen.add(f)) dump(q, f);
        }
        di.dispose();
        out.close();
    }

    private List<Function> resolve(String q) {
        List<Function> found = new ArrayList<>();
        FunctionManager fm = currentProgram.getFunctionManager();
        if (q.startsWith("str:")) {
            String needle = q.substring(4);
            for (Data d : currentProgram.getListing().getDefinedData(true)) {
                StringDataInstance s = StringDataInstance.getStringDataInstance(d);
                String v = s == StringDataInstance.NULL_INSTANCE ? null : s.getStringValue();
                if (v == null || !v.contains(needle)) continue;
                for (Reference r : getReferencesTo(d.getAddress())) {
                    Function f = fm.getFunctionContaining(r.getFromAddress());
                    out.println("STRING " + d.getAddress() + " \"" + v + "\" <- " + r.getFromAddress()
                            + (f == null ? "" : " in " + f.getName()));
                    if (f == null) out.println("  (ref site not inside a defined function; query its entry address)");
                    if (f != null && !found.contains(f)) found.add(f);
                }
            }
        } else if (q.startsWith("0x")) {
            Function f = fm.getFunctionContaining(toAddr(q));
            if (f == null) {
                // Stripped binaries often leave real functions (e.g. main) as labels; create one in-memory (-readOnly, not saved).
                disassemble(toAddr(q));
                f = createFunction(toAddr(q), null);
                if (f != null) out.println("NOTE created function at " + q + " (not saved)");
            }
            if (f != null) found.add(f);
        } else {
            for (Function f : fm.getFunctions(true))
                if (f.getName().equals(q) || f.getName(true).equals(q)) found.add(f);
        }
        return found;
    }

    private void dump(String q, Function f) throws Exception {
        out.println("==== QUERY " + q + " -> " + f.getName(true) + " @ " + f.getEntryPoint());
        out.println("SIG " + f.getPrototypeString(false, false));
        for (Reference r : getReferencesTo(f.getEntryPoint())) {
            if (!r.getReferenceType().isCall()) continue;
            Function c = getFunctionContaining(r.getFromAddress());
            out.println("CALLER " + r.getFromAddress() + " " + (c == null ? "?" : c.getName(true)));
        }
        for (Function c : f.getCalledFunctions(monitor))
            out.println("CALLEE " + c.getEntryPoint() + " " + c.getName(true) + (c.isExternal() ? " [ext]" : ""));
        if (f.isExternal() || f.isThunk()) return;
        DecompileResults r = di.decompileFunction(f, 120, monitor);
        out.println(r.decompileCompleted() ? r.getDecompiledFunction().getC()
                : "// decompile failed: " + r.getErrorMessage());
    }
}
