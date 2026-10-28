// Headless export: functions, strings, imports, and decompiled C into an output directory.
// Usage: analyzeHeadless ... -postScript ExportAll.java <outdir>
import ghidra.app.decompiler.*;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.data.StringDataInstance;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import java.io.*;
import java.nio.file.*;

public class ExportAll extends GhidraScript {
    @Override
    public void run() throws Exception {
        Path out = Paths.get(getScriptArgs()[0]);
        Files.createDirectories(out);
        Listing listing = currentProgram.getListing();

        try (PrintWriter fw = new PrintWriter(out.resolve("functions.tsv").toFile());
             PrintWriter cw = new PrintWriter(out.resolve("decompiled.c").toFile())) {
            DecompInterface di = new DecompInterface();
            di.openProgram(currentProgram);
            fw.println("entry\tname\tsize\tcallers");
            for (Function f : listing.getFunctions(true)) {
                if (monitor.isCancelled()) break;
                fw.printf("%s\t%s\t%d\t%d%n", f.getEntryPoint(), f.getName(),
                        f.getBody().getNumAddresses(), f.getCallingFunctions(monitor).size());
                if (f.isExternal() || f.isThunk()) continue;
                DecompileResults r = di.decompileFunction(f, 60, monitor);
                cw.printf("// %s @ %s%n", f.getName(), f.getEntryPoint());
                cw.println(r.decompileCompleted() ? r.getDecompiledFunction().getC()
                        : "// decompile failed: " + r.getErrorMessage());
            }
            di.dispose();
        }

        try (PrintWriter sw = new PrintWriter(out.resolve("strings.tsv").toFile())) {
            sw.println("address\tvalue");
            for (Data d : listing.getDefinedData(true)) {
                StringDataInstance s = StringDataInstance.getStringDataInstance(d);
                if (s != StringDataInstance.NULL_INSTANCE && s.getStringValue() != null)
                    sw.printf("%s\t%s%n", d.getAddress(), s.getStringValue().replace("\n", "\\n").replace("\t", "\\t"));
            }
        }

        try (PrintWriter iw = new PrintWriter(out.resolve("imports.tsv").toFile())) {
            iw.println("library\tname");
            for (Symbol s : currentProgram.getSymbolTable().getExternalSymbols())
                iw.printf("%s\t%s%n", s.getParentNamespace().getName(), s.getName());
        }
        println("ExportAll: wrote " + out);
    }
}
