import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Wrench, Send, Play, Save, Code, Loader2 } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";
import { useAuth } from "@/hooks/use-auth";
import HeaderNavbar from "@/components/HeaderNavbar";
import Breadcrumb from "@/components/Breadcrumb";

export default function Playground({ embedded = false }: { embedded?: boolean }) {
  const { isAuthenticated } = useAuth();
  const [userInput, setUserInput] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedCode, setGeneratedCode] = useState("");
  const [conversation, setConversation] = useState<Array<{ role: string, content: string }>>([]);

  const handleGenerate = async () => {
    if (!userInput.trim()) return;

    setIsGenerating(true);
    setConversation([...conversation, { role: "user", content: userInput }]);

    // Simulate AI response
    setTimeout(() => {
      const mockCode = `# Generated Tool: ${userInput}\n\nfrom typing import Dict, Any\n\ndef execute_tool(args: Dict[str, Any]) -> Dict[str, Any]:\n    \"\"\"\n    Auto-generated tool based on your request.\n    Args: ${userInput}\n    \"\"\"\n    # TODO: Implement tool logic\n    return {\n        "success": True,\n        "result": "Tool executed successfully"\n    }`;

      setGeneratedCode(mockCode);
      setConversation(prev => [...prev, {
        role: "assistant",
        content: `I've generated a Python tool template for "${userInput}". You can review and modify the code in the editor.`
      }]);
      setIsGenerating(false);
      setUserInput("");
      toast.success("Tool code generated!");
    }, 2000);
  };

  const handleTestTool = () => {
    toast.info("Testing tool...");
    setTimeout(() => {
      toast.success("Tool test completed successfully!");
    }, 1000);
  };

  const handleSaveTool = () => {
    toast.success("Tool saved to MCP server!");
  };

  return (
    <div className={embedded ? "h-full overflow-y-auto" : "min-h-screen"}>
      {!embedded && <HeaderNavbar variant="app" isAuthenticated={isAuthenticated} />}
      {!embedded && <Breadcrumb items={[
        { label: "Chat", path: "/" },
        { label: "Playground", path: "/playground" }
      ]} />}

      <div className={`container max-w-[90%] mx-auto px-6 mb-10 ${embedded ? "pt-8" : "pt-32"}`}>
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Playground</h1>
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Chat Interface */}
          <div className="space-y-4">
            <Card className="backdrop-blur-sm border-gray-400 shadow-xl">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-gray-900">
                  <Wrench className="h-5 w-5 text-brand" />
                  Tool Generator Chat
                </CardTitle>
                <CardDescription className="text-gray-900">Describe the tool you want to create</CardDescription>
              </CardHeader>
              <CardContent className="center_div">
                <ScrollArea className=" h-96 mb-4 rounded-lg border border-gray-400 bg-gray-200">
                  {conversation.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-center text-neutral-400">
                      <Wrench className="h-12 w-12 mb-4 text-brand" />
                      <p className="text-sm text-gray-900">Start by describing the tool you want to create</p>
                      <p className="text-xs mt-2 text-gray-900">Example: "Create a tool to fetch weather data"</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {conversation.map((msg, idx) => (
                        <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                          <div className={`max-w-[80%] rounded-lg p-3 ${msg.role === "user"
                              ? "bg-brand/50 text-gray-900"
                              : "bg-gray-300 border border-gray-400 text-gray-900"
                            }`}>
                            <p className="text-sm">{msg.content}</p>
                          </div>
                        </div>
                      ))}
                      {isGenerating && (
                        <div className="flex justify-start">
                          <div className="bg-brand border border-brand rounded-lg p-3">
                            <Loader2 className="h-4 w-4 animate-spin text-white" />
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </ScrollArea>

                <div className="flex gap-2">
                  <Input
                    placeholder="Describe your tool (e.g., 'Create a weather API tool')"
                    value={userInput}
                    onChange={(e) => setUserInput(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && handleGenerate()}
                    disabled={isGenerating}
                    className="bg-white border-gray-500 hover:border-brand text-gray-900 placeholder:text-gray-500"
                  />
                  <Button
                    onClick={handleGenerate}
                    disabled={isGenerating || !userInput.trim()}
                    className="bg-brand hover:bg-brand text-black border-0"
                  >
                    {isGenerating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Tool Examples */}
            <Card className="backdrop-blur-sm border-gray-400">
              <CardHeader>
                <CardTitle className="text-sm text-gray-900">Example Prompts</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {[
                  "Create a tool to search GitHub repositories",
                  "Build a calculator tool with basic operations",
                  "Make a tool to convert currencies",
                  "Create a tool to validate email addresses"
                ].map((example, idx) => (
                  <button
                    key={idx}
                    onClick={() => setUserInput(example)}
                    className="w-full text-left py-2 px-3 rounded-lg bg-gray-300 border border-gray-400 text-gray-900 hover:bg-gray-400"
                  >
                    {example}
                  </button>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Code Editor */}
          <div className="space-y-4">
            <Card className="backdrop-blur-sm border-gray-400">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2 text-gray-900">
                      <Code className="h-5 w-5 text-brand" />
                      Generated Code
                    </CardTitle>
                    <CardDescription className="text-gray-900">Review and edit the generated tool code</CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleTestTool}
                      disabled={!generatedCode}
                      className="text-[#756200] border-brand text-sm px-4 hover:bg-brand hover:text-black shadow-xl"
                    >
                      <Play className="h-4 w-4" />
                      Test
                    </Button>
                    <Button
                      size="sm"
                      onClick={handleSaveTool}
                      disabled={!generatedCode}
                      className="bg-brand hover:bg-brand/90 transition-all text-black border-0 shadow-xl"
                    >
                      <Save className="h-4 w-4" />
                      Save
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {generatedCode ? (
                  <Textarea
                    value={generatedCode}
                    onChange={(e) => setGeneratedCode(e.target.value)}
                    className="h-125 font-mono bg-white border-gray-500 hover:border-brand text-gray-900 placeholder:text-gray-500"
                  />
                ) : (
                  <div className="h-125 flex items-center justify-center border border-dashed border-neutral-800 rounded-lg bg-gray-200">
                    <div className="text-center text-neutral-400">
                      <Code className="h-12 w-12 mx-auto mb-4 text-brand" />
                      <p className="text-sm text-gray-900">Generated code will appear here</p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Tool Metadata */}
            {generatedCode && (
              <Card className="backdrop-blur-sm border-gray-400">
                <CardHeader>
                  <CardTitle className="text-gray-900">Tool Metadata</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div>
                    <label className="text-xs font-medium text-gray-900">Tool Name</label>
                    <Input placeholder="my_custom_tool" className="bg-white border-gray-500 hover:border-brand text-gray-900 placeholder:text-gray-500" />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-900">Description</label>
                    <Input placeholder="Tool description" className="bg-white border-gray-500 hover:border-brand text-gray-900 placeholder:text-gray-500" />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-900">Category</label>
                    <Input placeholder="utility, data, integration" className="bg-white border-gray-500 hover:border-brand text-gray-900 placeholder:text-gray-500" />
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
