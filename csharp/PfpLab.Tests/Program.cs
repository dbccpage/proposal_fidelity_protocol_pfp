// AuthorityEffect: None.
// Contract: urn:pfp-lab:csharp:tests:program:v1
// `dotnet run --project csharp/PfpLab.Tests [-- --unit]`: every test, or only
// the ones that start no process.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace PfpLab.Tests;

internal static class Program
{
    [STAThread]
    public static int Main(string[] args)
    {
        bool unitOnly = args.Contains("--unit", StringComparer.Ordinal);
        IEnumerable<TestCase> cases = UnitTests.All().Concat(ViewModelTests.All());
        if (!unitOnly)
        {
            cases = cases.Concat(ContractTests.All());
        }

        return Task.Run(() => Runner.RunAsync(cases)).GetAwaiter().GetResult();
    }
}
