import { useAuth } from "@/hooks/use-auth";
import { useNavigate } from "react-router";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { LogOut, User, Settings } from "lucide-react";
import { getInitials } from "@/lib/utils";

export default function LogoutButton() {
  const { user, signOut, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  if (!isAuthenticated || !user) {
    return null;
  }

  const handleSignOut = async () => {
    await signOut();
    navigate("/login");
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          className="flex items-center gap-2 p-0 outline-0 text-[#171717] hover:text-[#171717]/80 hover:bg-[#171717]/5 rounded-2xl transition-colors"
        >
          <div className="h-10 w-10 rounded-full bg-gradient-to-br from-[#171717] to-[#404040] border-2 border-[#171717]/20 flex items-center justify-center text-white text-sm font-bold shadow-md">
            {getInitials(user.name)}
          </div>
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-56 bg-gradient-to-br from-[#fffeff] to-[#f8f8f6] border-2 border-[#171717]/20 shadow-xl backdrop-blur-sm rounded-xl p-2">
        <div className="text-left text-[#171717] hidden md:block px-3 py-3 rounded-lg bg-white/50">
          <p className="text-base font-semibold text-[#171717]">{user.name || user.user_id}</p>
          <p className="text-xs text-gray-600 mt-0.5">{user.email}</p>
        </div>
        <DropdownMenuSeparator className="bg-[#171717]/10 my-1" />
        <DropdownMenuItem className="text-[#171717] focus:bg-[#171717]/10 cursor-pointer rounded-lg py-2.5 px-3 my-0.5 transition-colors">
          <User className="mr-2 h-4 w-4" />
          <span>Profile</span>
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => navigate("/agents/settings")}
          className="text-[#171717] focus:bg-[#171717]/10 cursor-pointer rounded-lg py-2.5 px-3 my-0.5 transition-colors"
        >
          <Settings className="mr-2 h-4 w-4" />
          <span>Settings</span>
        </DropdownMenuItem>
        <DropdownMenuSeparator className="bg-[#171717]/10 my-1" />
        <DropdownMenuItem
          onClick={handleSignOut}
          className="text-white justify-center bg-red-500 hover:bg-red-600 cursor-pointer rounded-lg py-2.5 px-3 my-0.5 transition-colors font-medium"
        >
          <LogOut className="mr-2 h-4 w-4" />
          <span>Logout</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
