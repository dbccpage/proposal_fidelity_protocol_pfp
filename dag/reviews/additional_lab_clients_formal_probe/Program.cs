using System.Text.Json;
using PfpLab.Client;
var body=File.ReadAllText(Path.Combine(AppContext.BaseDirectory,"../../../receipt.json"));
var options=new JsonSerializerOptions {PropertyNamingPolicy=JsonNamingPolicy.SnakeCaseLower};
var receipt=JsonSerializer.Deserialize<Receipt>(body,options) ?? throw new Exception("no receipt");
try { receipt.Validate(); Console.WriteLine("large_valid_python_receipt=accepted"); }
catch(CoreException ex) { Console.WriteLine("large_valid_python_receipt="+ex.Kind+":"+ex.Message); }
// Direct DTO validation demonstrates the hash alphabet gap, independent of semantic replay.
var forged=receipt with {Digest=new string('z',64),Verdicts=Array.Empty<Verdict>(),Final=new FinalState(new Dictionary<string,string>(),Array.Empty<Claim>(),"0","0")};
try { forged.Validate(); Console.WriteLine("nonhex_digest_dto=accepted"); }
catch(CoreException ex) { Console.WriteLine("nonhex_digest_dto="+ex.Kind); }
